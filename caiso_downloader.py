#!/usr/bin/env python3
"""
CAISO OASIS System Demand Downloader

This script downloads system demand data from the CAISO OASIS API.
It supports DA, 2DA, and 7DA market runs with flexible date input and configuration file options.
"""

import requests
import argparse
import configparser
import os
import sys
from datetime import datetime, timedelta
from dateutil import parser as date_parser
import zipfile
import logging
import pandas as pd
import tempfile
import shutil
import time
import random
import xml.etree.ElementTree as ET
from io import StringIO

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CAISODownloader:
    def __init__(self, config_file='config.ini'):
        """Initialize the CAISO downloader with configuration."""
        self.config = self._load_config(config_file)
        self.session = requests.Session()
        self.max_days_per_chunk = 30  # Maximum days per download chunk
        
        # Rate limiting settings
        self.rate_limit_delay = 5  # Base delay between requests (seconds)
        self.max_retries = 3  # Maximum number of retries per chunk
        self.exponential_backoff = True  # Use exponential backoff for retries
        
    def _load_config(self, config_file):
        """Load configuration from file."""
        config = configparser.ConfigParser()
        
        if os.path.exists(config_file):
            config.read(config_file)
            logger.info(f"Configuration loaded from {config_file}")
        else:
            logger.warning(f"Config file {config_file} not found. Using default values.")
            # Set default values
            config['CAISO_OASIS'] = {
                'default_start_date': '20130919T07:00-0000',
                'default_end_date': '20130920T07:00-0000',
                'base_url': 'http://oasis.caiso.com/oasisapi/SingleZip',
                'query_name': 'SLD_FCST',
                'market_run_id': '2DA',
                'version': '1',
                'output_directory': './downloads',
                'data_directory': './data',
                'output_filename_format': 'system_demand_{market_run}_{start_date}_{end_date}.zip',
                'csv_filename_format': 'system_demand_{market_run}_{start_date}_{end_date}.csv',
                'extract_and_parse': 'true',
                'max_days_per_chunk': '30',
                'rate_limit_delay': '5',
                'max_retries': '3'
            }
        
        return config
    
    def validate_market_run(self, market_run):
        """Validate market run ID."""
        valid_runs = ['DA', '2DA', '7DA']
        if market_run.upper() not in valid_runs:
            raise ValueError(f"Invalid market run: {market_run}. Valid options are: {', '.join(valid_runs)}")
        return market_run.upper()
    
    def validate_date_format(self, date_str):
        """Validate and format date string."""
        try:
            # Parse the date string
            parsed_date = date_parser.parse(date_str)
            # Format as required by CAISO API: YYYYMMDDTHH:MM-0000
            formatted_date = parsed_date.strftime('%Y%m%dT%H:%M-0000')
            return formatted_date
        except ValueError as e:
            raise ValueError(f"Invalid date format: {date_str}. Expected format: YYYY-MM-DD or YYYY-MM-DD HH:MM")
    
    def parse_date_to_datetime(self, date_str):
        """Parse date string to datetime object."""
        try:
            return date_parser.parse(date_str)
        except ValueError as e:
            raise ValueError(f"Invalid date format: {date_str}. Expected format: YYYY-MM-DD or YYYY-MM-DD HH:MM")
    
    def format_date_for_api(self, dt):
        """Format datetime object for CAISO API."""
        return dt.strftime('%Y%m%dT%H:%M-0000')
    
    def create_date_chunks(self, start_date, end_date):
        """Create date chunks of maximum 30 days each."""
        start_dt = self.parse_date_to_datetime(start_date)
        end_dt = self.parse_date_to_datetime(end_date)
        
        # Calculate total days difference
        total_days = (end_dt - start_dt).days
        
        if total_days <= self.max_days_per_chunk:
            # No chunking needed
            return [(start_date, end_date)]
        
        logger.info(f"Date range spans {total_days} days. Breaking into chunks of maximum {self.max_days_per_chunk} days.")
        
        chunks = []
        current_start = start_dt
        
        while current_start < end_dt:
            # Calculate chunk end date (max 30 days from current start)
            chunk_end = min(current_start + timedelta(days=self.max_days_per_chunk), end_dt)
            
            # Format dates for API
            chunk_start_str = self.format_date_for_api(current_start)
            chunk_end_str = self.format_date_for_api(chunk_end)
            
            chunks.append((chunk_start_str, chunk_end_str))
            
            # Move to next chunk
            current_start = chunk_end
        
        logger.info(f"Created {len(chunks)} chunks:")
        for i, (chunk_start, chunk_end) in enumerate(chunks, 1):
            logger.info(f"  Chunk {i}: {chunk_start} to {chunk_end}")
        
        return chunks
    
    def build_url(self, start_date, end_date, market_run):
        """Build the CAISO OASIS API URL."""
        base_url = self.config['CAISO_OASIS']['base_url']
        query_name = self.config['CAISO_OASIS']['query_name']
        version = self.config['CAISO_OASIS']['version']
        
        # Map user-friendly market run names to API identifiers
        market_run_mapping = {
            'DA': 'DAM',  # Day Ahead Market
            '2DA': '2DA', # 2-Day Ahead
            '7DA': '7DA'  # 7-Day Ahead
        }
        
        # Use the mapped value or the original if not in mapping
        api_market_run = market_run_mapping.get(market_run, market_run)
        
        # Build URL with parameters
        url = (f"{base_url}?queryname={query_name}&market_run_id={api_market_run}"
               f"&startdatetime={start_date}&enddatetime={end_date}&version={version}")
        
        return url
    
    def parse_xml_to_dataframe(self, xml_content):
        """Parse XML content and extract relevant records to DataFrame."""
        try:
            # Parse XML
            root = ET.fromstring(xml_content)
            
            # Define the namespace if present
            namespaces = {
                'ns': 'http://www.caiso.com/soa/OASISReport_v1.xsd'
            }
            
            # Try to find data records - adjust these paths based on actual XML structure
            records = []
            
            # Common paths for CAISO OASIS data
            possible_paths = [
                './/ns:REPORT_DATA',
                './/REPORT_DATA',
                './/ns:DataRow',
                './/DataRow',
                './/ns:row',
                './/row',
                './/ns:record',
                './/record'
            ]
            
            data_elements = None
            for path in possible_paths:
                try:
                    if path.startswith('.//ns:'):
                        data_elements = root.findall(path, namespaces)
                    else:
                        data_elements = root.findall(path)
                    if data_elements:
                        logger.info(f"Found data using path: {path}")
                        break
                except Exception:
                    continue
            
            if not data_elements:
                # If no specific data elements found, try to extract all elements with data
                logger.warning("No standard data elements found, attempting to extract all elements")
                data_elements = root.findall('.//*')
            
            for element in data_elements:
                record = {}
                
                # Extract attributes
                for attr_name, attr_value in element.attrib.items():
                    record[attr_name] = attr_value
                
                # Extract text content
                if element.text and element.text.strip():
                    record['text'] = element.text.strip()
                
                # Extract child elements
                for child in element:
                    tag = child.tag.replace('{http://www.caiso.com/soa/OASISReport_v1.xsd}', '')
                    if child.text and child.text.strip():
                        record[tag] = child.text.strip()
                    elif child.attrib:
                        record[tag] = child.attrib
                
                if record:  # Only add non-empty records
                    records.append(record)
            
            if not records:
                logger.warning("No records extracted from XML")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(records)
            logger.info(f"Extracted {len(df)} records with {len(df.columns)} columns")
            logger.info(f"Columns: {list(df.columns)}")
            
            return df
            
        except ET.ParseError as e:
            logger.error(f"XML parsing error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing XML: {e}")
            return None
    
    def extract_and_parse_zip(self, zip_path, output_dir, market_run):
        """Extract ZIP file and parse XML data into CSV format."""
        logger.info(f"Extracting and parsing ZIP file: {zip_path}")
        
        # Create temporary directory for extraction
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Extract ZIP file
                with zipfile.ZipFile(zip_path, 'r') as zip_file:
                    zip_file.extractall(temp_dir)
                    extracted_files = zip_file.namelist()
                
                logger.info(f"Extracted {len(extracted_files)} files")
                
                # Find XML files in the extracted content
                xml_files = [f for f in extracted_files if f.lower().endswith('.xml')]
                
                if not xml_files:
                    logger.warning("No XML files found in the ZIP archive")
                    # List all extracted files for debugging
                    logger.info(f"Extracted files: {extracted_files}")
                    return None
                
                # Parse and combine all XML files
                all_data = []
                for xml_file in xml_files:
                    xml_path = os.path.join(temp_dir, xml_file)
                    try:
                        # Read XML file with different encodings
                        xml_content = None
                        for encoding in ['utf-8', 'latin-1', 'cp1252']:
                            try:
                                with open(xml_path, 'r', encoding=encoding) as f:
                                    xml_content = f.read()
                                logger.info(f"Successfully read {xml_file} with {encoding} encoding")
                                break
                            except UnicodeDecodeError:
                                continue
                        
                        if xml_content is None:
                            logger.warning(f"Could not decode {xml_file} with any encoding")
                            continue
                        
                        # Parse XML content
                        df = self.parse_xml_to_dataframe(xml_content)
                        if df is not None and not df.empty:
                            all_data.append(df)
                            logger.info(f"Successfully parsed {xml_file}")
                        else:
                            logger.warning(f"No data extracted from {xml_file}")
                            
                    except Exception as e:
                        logger.error(f"Error parsing {xml_file}: {e}")
                
                if not all_data:
                    logger.error("No data could be parsed from the ZIP file")
                    return None
                
                # Combine all dataframes
                if len(all_data) == 1:
                    combined_df = all_data[0]
                else:
                    combined_df = pd.concat(all_data, ignore_index=True)
                
                logger.info(f"Combined data shape: {combined_df.shape}")
                
                # Generate CSV filename with market run - simplified naming
                # Extract start and end dates from the ZIP filename
                zip_basename = os.path.basename(zip_path)
                
                # Remove chunk info if present
                if zip_basename.startswith('chunk_'):
                    # Extract the part after chunk info
                    parts = zip_basename.split('_', 4)  # Split on first 4 underscores
                    if len(parts) >= 5:
                        # Reconstruct filename without chunk info
                        zip_basename = '_'.join(parts[4:])
                
                # Remove .zip extension and clean up dates
                csv_basename = zip_basename.replace('.zip', '')
                
                # Remove -0000 from dates
                csv_basename = csv_basename.replace('-0000', '')
                
                # Ensure .csv extension
                if not csv_basename.endswith('.csv'):
                    csv_basename += '.csv'
                
                csv_path = os.path.join(output_dir, csv_basename)
                
                # Remove existing CSV file if it exists
                if os.path.exists(csv_path):
                    os.remove(csv_path)
                    logger.info(f"Removed existing CSV file: {csv_path}")
                
                # Save to CSV
                combined_df.to_csv(csv_path, index=False)
                logger.info(f"Data saved to CSV: {csv_path}")
                
                # Show data summary
                logger.info(f"CSV file contains {len(combined_df)} rows and {len(combined_df.columns)} columns")
                logger.info(f"Columns: {list(combined_df.columns)}")
                
                # Show sample data
                if not combined_df.empty:
                    logger.info("Sample data (first 3 rows):")
                    logger.info(combined_df.head(3).to_string())
                
                return csv_path
                
            except zipfile.BadZipFile:
                logger.error("Invalid ZIP file")
                return None
            except Exception as e:
                logger.error(f"Error extracting/parsing ZIP file: {e}")
                return None
    
    def download_with_retry(self, url, output_path, chunk_info=""):
        """Download with retry logic and rate limiting."""
        for attempt in range(self.max_retries + 1):
            try:
                # Add rate limiting delay between requests
                if attempt > 0:
                    delay = self.rate_limit_delay * (2 ** (attempt - 1)) if self.exponential_backoff else self.rate_limit_delay
                    delay += random.uniform(0, 2)  # Add jitter to avoid thundering herd
                    logger.info(f"{chunk_info} Retry {attempt}/{self.max_retries} in {delay:.1f} seconds...")
                    time.sleep(delay)
                
                # Download the data
                response = self.session.get(url, stream=True, timeout=60)
                
                # Handle specific HTTP errors
                if response.status_code == 429:
                    logger.warning(f"{chunk_info} Rate limited (429). Retrying...")
                    continue
                elif response.status_code == 503:
                    logger.warning(f"{chunk_info} Service temporarily unavailable (503). Retrying...")
                    continue
                elif response.status_code >= 400:
                    response.raise_for_status()
                
                # Save the file
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                logger.info(f"{chunk_info} Download completed successfully on attempt {attempt + 1}")
                return True
                
            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries:
                    logger.warning(f"{chunk_info} Download attempt {attempt + 1} failed: {e}")
                    continue
                else:
                    logger.error(f"{chunk_info} All download attempts failed: {e}")
                    return False
        
        return False
    
    def download_single_chunk(self, start_date, end_date, output_dir, market_run, chunk_index=None, total_chunks=None):
        """Download a single chunk of data with retry logic."""
        chunk_info = f" (chunk {chunk_index}/{total_chunks})" if chunk_index and total_chunks else ""
        logger.info(f"Downloading {market_run} chunk{chunk_info}: {start_date} to {end_date}")
        
        # Build the URL
        url = self.build_url(start_date, end_date, market_run)
        
        # Generate output filename for this chunk
        filename_format = self.config['CAISO_OASIS']['output_filename_format']
        start_date_clean = start_date.replace(':', '').replace('-0000', '')
        end_date_clean = end_date.replace(':', '').replace('-0000', '')
        
        if chunk_index and total_chunks:
            # Add chunk info to filename
            output_filename = f"chunk_{chunk_index:02d}_of_{total_chunks:02d}_{filename_format.format(market_run=market_run, start_date=start_date_clean, end_date=end_date_clean)}"
        else:
            output_filename = filename_format.format(market_run=market_run, start_date=start_date_clean, end_date=end_date_clean)
        
        output_path = os.path.join(output_dir, output_filename)
        
        # Download with retry logic
        if self.download_with_retry(url, output_path, chunk_info):
            # Verify it's a valid ZIP file
            try:
                with zipfile.ZipFile(output_path, 'r') as zip_file:
                    file_list = zip_file.namelist()
                    logger.info(f"{market_run} chunk{chunk_info} ZIP contains {len(file_list)} files")
                    # Show XML files if present
                    xml_files = [f for f in file_list if f.lower().endswith('.xml')]
                    if xml_files:
                        logger.info(f"{market_run} chunk{chunk_info} XML files: {xml_files}")
                return output_path
            except zipfile.BadZipFile:
                logger.warning(f"{market_run} chunk{chunk_info} downloaded file is not a valid ZIP file")
                return None
        else:
            return None
    
    def download_data(self, start_date=None, end_date=None, output_dir=None, data_dir=None, market_run='2DA', extract_and_parse=True):
        """Download system demand data from CAISO OASIS."""
        
        # Validate market run
        market_run = self.validate_market_run(market_run)
        
        # Use provided dates or defaults from config
        if start_date is None:
            start_date = self.config['CAISO_OASIS']['default_start_date']
        else:
            start_date = self.validate_date_format(start_date)
            
        if end_date is None:
            end_date = self.config['CAISO_OASIS']['default_end_date']
        else:
            end_date = self.validate_date_format(end_date)
        
        # Use provided output directory or default from config
        if output_dir is None:
            output_dir = self.config['CAISO_OASIS']['output_directory']
        
        # Use provided data directory or default from config
        if data_dir is None:
            data_dir = self.config['CAISO_OASIS']['data_directory']
        
        # Create output directories if they don't exist
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(data_dir, exist_ok=True)
        
        # Create date chunks
        date_chunks = self.create_date_chunks(start_date, end_date)
        
        # Download each chunk with rate limiting
        downloaded_files = []
        successful_downloads = 0
        
        for i, (chunk_start, chunk_end) in enumerate(date_chunks, 1):
            # Add delay between chunks to respect rate limits
            if i > 1:
                delay = self.rate_limit_delay + random.uniform(0, 2)
                logger.info(f"Waiting {delay:.1f} seconds before next chunk...")
                time.sleep(delay)
            
            chunk_file = self.download_single_chunk(
                chunk_start, 
                chunk_end, 
                output_dir, 
                market_run,
                chunk_index=i, 
                total_chunks=len(date_chunks)
            )
            
            if chunk_file:
                downloaded_files.append(chunk_file)
                successful_downloads += 1
            else:
                logger.error(f"Failed to download chunk {i}/{len(date_chunks)}")
        
        if successful_downloads == 0:
            logger.error("No chunks were downloaded successfully")
            return None
        
        logger.info(f"Successfully downloaded {successful_downloads}/{len(date_chunks)} chunks")
        
        # Extract and parse if requested
        csv_files = []
        if extract_and_parse:
            for zip_file in downloaded_files:
                csv_file = self.extract_and_parse_zip(zip_file, data_dir, market_run)
                if csv_file:
                    csv_files.append(csv_file)
        
        return {
            'zip_files': downloaded_files,
            'csv_files': csv_files,
            'total_chunks': len(date_chunks),
            'successful_chunks': successful_downloads,
            'market_run': market_run
        }
    
    def get_available_dates(self):
        """Get available date range information."""
        logger.info("CAISO OASIS API typically provides data for:")
        logger.info("- Historical data: Available for past dates")
        logger.info("- Current data: Available for recent dates")
        logger.info("- Forecast data: Available for future dates")
        logger.info("- Market runs: DA (Day Ahead), 2DA (2-Day Ahead), 7DA (7-Day Ahead)")
        logger.info(f"- Maximum recommended download period: {self.max_days_per_chunk} days")
        logger.info(f"- Rate limiting: {self.rate_limit_delay}s delay between requests")
        logger.info(f"- Retry attempts: {self.max_retries} per chunk")
        logger.info("- Data format: XML files in ZIP archives")
        logger.info("Note: Data availability may vary. Check CAISO OASIS website for current availability.")

def main():
    """Main function to handle command-line interface."""
    parser = argparse.ArgumentParser(
        description='Download system demand data from CAISO OASIS API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use dates from config file (default: 2DA)
  python caiso_downloader.py
  
  # Use custom date range with 2DA (default)
  python caiso_downloader.py --start-date 2023-09-19 --end-date 2023-10-20
  
  # Use custom date range with DA
  python caiso_downloader.py --start-date 2023-09-19 --end-date 2023-10-20 --market-run DA
  
  # Use custom date range with 7DA
  python caiso_downloader.py --start-date 2023-09-19 --end-date 2023-10-20 --market-run 7DA
  
  # Use custom date range with time
  python caiso_downloader.py --start-date "2023-09-19 07:00" --end-date "2023-09-20 07:00"
  
  # Specify custom output directory
  python caiso_downloader.py --output-dir ./my_downloads
  
  # Use custom config file
  python caiso_downloader.py --config my_config.ini
  
  # Download only (no extraction/parsing)
  python caiso_downloader.py --no-parse
        """
    )
    
    parser.add_argument('--start-date', 
                       help='Start date (YYYY-MM-DD or YYYY-MM-DD HH:MM)')
    parser.add_argument('--end-date', 
                       help='End date (YYYY-MM-DD or YYYY-MM-DD HH:MM)')
    parser.add_argument('--output-dir', 
                       help='Output directory for downloaded ZIP files')
    parser.add_argument('--data-dir', 
                       help='Output directory for CSV files (default: ./data)')
    parser.add_argument('--market-run', 
                       choices=['DA', '2DA', '7DA'],
                       default='2DA',
                       help='Market run type: DA (Day Ahead), 2DA (2-Day Ahead), 7DA (7-Day Ahead)')
    parser.add_argument('--config', 
                       default='config.ini',
                       help='Configuration file path (default: config.ini)')
    parser.add_argument('--info', 
                       action='store_true',
                       help='Show information about available data')
    parser.add_argument('--no-parse', 
                       action='store_true',
                       help='Download ZIP file only, do not extract and parse to CSV')
    
    args = parser.parse_args()
    
    try:
        # Initialize downloader
        downloader = CAISODownloader(args.config)
        
        if args.info:
            downloader.get_available_dates()
            return
        
        # Download data
        result = downloader.download_data(
            start_date=args.start_date,
            end_date=args.end_date,
            output_dir=args.output_dir,
            data_dir=args.data_dir,
            market_run=args.market_run,
            extract_and_parse=not args.no_parse
        )
        
        if result:
            print(f"\n✅ Download successful!")
            print(f"📦 Downloaded {result['successful_chunks']}/{result['total_chunks']} chunks for {result['market_run']}")
            print(f"📁 ZIP files saved to: {args.output_dir or './downloads'}")
            if result['csv_files']:
                print(f"📊 CSV files saved to: {args.data_dir or './data'}")
                print(f"📊 CSV files created: {len(result['csv_files'])} files")
        else:
            print("\n❌ Download failed. Check the logs above for details.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 