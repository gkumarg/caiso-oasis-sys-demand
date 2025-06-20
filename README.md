# CAISO OASIS System Demand Downloader

This tool downloads system demand data from the CAISO OASIS API. It supports DA, 2DA, and 7DA market runs with flexible date input and configuration file options.

## Features

- Download system demand data from CAISO OASIS API
- **NEW**: Support for multiple market runs: DA (Day Ahead), 2DA (2-Day Ahead), 7DA (7-Day Ahead)
- **NEW**: Automatically extract ZIP files and parse XML data to CSV format
- **NEW**: Automatic chunking of large date ranges (max 30 days per chunk)
- **NEW**: Rate limiting and retry logic to handle API limits (429 errors)
- Support for both user input dates and configuration file defaults
- Flexible date format parsing (YYYY-MM-DD or YYYY-MM-DD HH:MM)
- Automatic output directory creation
- ZIP file validation and content listing
- **NEW**: XML to CSV conversion with logical naming
- **NEW**: Automatic removal of existing CSV files before creating new ones
- **NEW**: Chunked downloads with progress tracking
- **NEW**: Exponential backoff retry strategy
- **NEW**: Separate data directory for CSV files
- Comprehensive logging and error handling
- Configurable output file naming

## Installation

1. Clone or download this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

The tool uses a `config.ini` file for default settings. You can modify this file to change:

- Default start and end dates
- API settings
- Output directory and filename format
- XML extraction settings
- Maximum days per chunk (default: 30)
- Rate limiting settings (delay, retries)

### Example config.ini:
```ini
[CAISO_OASIS]
# Default date range for system demand downloads
# Format: YYYYMMDDTHH:MM-0000 (UTC timezone)
default_start_date = 20130919T07:00-0000
default_end_date = 20130920T07:00-0000

# API settings
base_url = http://oasis.caiso.com/oasisapi/SingleZip
query_name = SLD_FCST
market_run_id = 2DA
version = 1

# Output settings
output_directory = ./downloads
data_directory = ./data
output_filename_format = system_demand_{market_run}_{start_date}_{end_date}.zip
csv_filename_format = system_demand_{market_run}_{start_date}_{end_date}.csv
extract_and_parse = true

# Chunking and rate limiting settings
max_days_per_chunk = 30
rate_limit_delay = 5
max_retries = 3
```

## Usage

### Basic Usage (using config file defaults - 2DA)
```bash
python caiso_downloader.py
```
This will download the ZIP file and automatically extract/parse XML data to CSV.

### Market Run Options

#### Day Ahead (DA)
```bash
python caiso_downloader.py --market-run DA --start-date 2023-09-19 --end-date 2023-09-20
```

#### 2-Day Ahead (2DA) - Default
```bash
python caiso_downloader.py --market-run 2DA --start-date 2023-09-19 --end-date 2023-10-20
```

#### 7-Day Ahead (7DA)
```bash
python caiso_downloader.py --market-run 7DA --start-date 2023-09-19 --end-date 2023-09-20
```

### Custom Date Range (with automatic chunking)
```bash
# Date only (will be chunked if > 30 days)
python caiso_downloader.py --start-date 2023-09-19 --end-date 2023-10-20

# Date with time
python caiso_downloader.py --start-date "2023-09-19 07:00" --end-date "2023-09-20 07:00"
```

### Custom Output Directories
```bash
# Custom ZIP directory
python caiso_downloader.py --output-dir ./my_downloads

# Custom CSV directory
python caiso_downloader.py --data-dir ./my_data

# Both custom directories
python caiso_downloader.py --output-dir ./my_downloads --data-dir ./my_data
```

### Download ZIP Only (No XML Extraction)
```bash
python caiso_downloader.py --no-parse
```

### Custom Configuration File
```bash
python caiso_downloader.py --config my_config.ini
```

### Show Information About Available Data
```bash
python caiso_downloader.py --info
```

### Help
```bash
python caiso_downloader.py --help
```

## Market Run Types

The tool supports three types of market runs:

### DA (Day Ahead)
- **Description**: Day-ahead system demand forecasts
- **Use case**: Planning for next day operations
- **Data availability**: Available for historical and current dates

### 2DA (2-Day Ahead) - Default
- **Description**: 2-day ahead system demand forecasts
- **Use case**: Medium-term planning and analysis
- **Data availability**: Available for historical and current dates

### 7DA (7-Day Ahead)
- **Description**: 7-day ahead system demand forecasts
- **Use case**: Long-term planning and trend analysis
- **Data availability**: Available for historical and current dates

**Note**: The "DA" option internally maps to "DAM" (Day Ahead Market) in the CAISO OASIS API, which is the correct identifier for Day Ahead data.

## Rate Limiting and Retry Logic

The tool includes robust rate limiting and retry mechanisms to handle API limits:

### Rate Limiting Features
- **Base delay**: 5 seconds between requests (configurable)
- **Jitter**: Random delay variation to avoid thundering herd
- **Chunk delays**: Automatic delays between chunk downloads
- **Configurable**: Adjust `rate_limit_delay` in config.ini

### Retry Logic
- **Max retries**: 3 attempts per chunk (configurable)
- **Exponential backoff**: Increasing delays between retries
- **Specific error handling**: 
  - 429 (Too Many Requests): Automatic retry
  - 503 (Service Unavailable): Automatic retry
  - Other 4xx/5xx errors: Proper error reporting
- **Timeout**: 60-second timeout per request

### Example Retry Behavior
```
Attempt 1: Immediate download
Attempt 2: Wait 5-7 seconds (base delay + jitter)
Attempt 3: Wait 10-12 seconds (2x base delay + jitter)
```

## Automatic Chunking

The tool automatically breaks down large date ranges into smaller chunks to avoid download errors:

- **Maximum chunk size**: 30 days (configurable)
- **Automatic detection**: Date ranges > 30 days are automatically chunked
- **Progress tracking**: Shows download progress for each chunk
- **Error handling**: Continues downloading other chunks if one fails
- **File naming**: Chunked files include chunk information in filename

### Example Chunking
For a 90-day date range (2023-09-01 to 2023-12-01), the tool will create:
- Chunk 1: 2023-09-01 to 2023-10-01 (30 days)
- Chunk 2: 2023-10-01 to 2023-11-01 (30 days)  
- Chunk 3: 2023-11-01 to 2023-12-01 (30 days)

### Chunked File Naming
```
chunk_01_of_03_system_demand_2DA_20230901T0700-0000_20231001T0700-0000.zip
chunk_02_of_03_system_demand_2DA_20231001T0700-0000_20231101T0700-0000.zip
chunk_03_of_03_system_demand_2DA_20231101T0700-0000_20231201T0700-0000.zip
```

### CSV File Naming (Simplified)
```
system_demand_2DA_20230901T0700_20231001T0700.csv
system_demand_2DA_20231001T0700_20231101T0700.csv
system_demand_2DA_20231101T0700_20231201T0700.csv
```

## API URL Format

The tool constructs URLs in the following format:
```
http://oasis.caiso.com/oasisapi/SingleZip?queryname=SLD_FCST&market_run_id={MARKET_RUN}&startdatetime=YYYYMMDDTHH:MM-0000&enddatetime=YYYYMMDDTHH:MM-0000&version=1
```

Where `{MARKET_RUN}` can be `DA`, `2DA`, or `7DA`.

## Output

### ZIP Files
- Downloaded files are saved as ZIP files in the specified output directory
- Files are automatically named using the format: `system_demand_{market_run}_{start_date}_{end_date}.zip`
- Chunked downloads include chunk information in filenames
- The tool validates ZIP files and shows their contents
- **NEW**: Lists XML files found in each ZIP archive

### CSV Files (NEW)
- **Automatic extraction**: ZIP files are automatically extracted and XML data parsed
- **Logical naming**: CSV files use the same naming convention as ZIP files but with `.csv` extension
- **File replacement**: Existing CSV files are automatically removed before creating new ones
- **Multiple encodings**: Supports UTF-8, Latin-1, and CP1252 encodings for XML files
- **Data combination**: If multiple XML files are found in the ZIP, they are combined into a single CSV
- **Data summary**: Shows row count, column count, and column names
- **Sample data**: Displays first 3 rows of extracted data for verification
- **Data directory**: CSV files are saved to the `./data` directory by default

### Example Output Structure
```
downloads/
├── chunk_01_of_03_system_demand_2DA_20230901T0700-0000_20231001T0700-0000.zip
├── chunk_02_of_03_system_demand_2DA_20231001T0700-0000_20231101T0700-0000.zip
└── chunk_03_of_03_system_demand_2DA_20231101T0700-0000_20231201T0700-0000.zip

data/
├── chunk_01_of_03_system_demand_2DA_20230901T0700-0000_20231001T0700-0000.csv
├── chunk_02_of_03_system_demand_2DA_20231001T0700-0000_20231101T0700-0000.csv
└── chunk_03_of_03_system_demand_2DA_20231101T0700-0000_20231201T0700-0000.csv
```

## XML Processing Features

- **Automatic extraction**: No manual ZIP extraction required
- **Encoding detection**: Automatically tries multiple encodings (UTF-8, Latin-1, CP1252)
- **Namespace handling**: Supports CAISO OASIS XML namespaces
- **Flexible parsing**: Tries multiple XML paths to find data records
- **Data extraction**: Extracts attributes, text content, and child elements
- **Error handling**: Graceful handling of parsing errors with detailed logging
- **Data validation**: Shows data shape and column information after processing
- **Clean replacement**: Removes existing CSV files before creating new ones
- **Sample preview**: Shows sample data for verification

### XML Parsing Strategy
The tool uses a flexible approach to parse CAISO OASIS XML files:

1. **Namespace support**: Handles CAISO OASIS XML namespaces
2. **Multiple paths**: Tries common XML paths for data records:
   - `REPORT_DATA`
   - `DataRow`
   - `row`
   - `record`
3. **Fallback parsing**: If standard paths fail, extracts all elements with data
4. **Comprehensive extraction**: Captures attributes, text content, and child elements

## Error Handling

The tool includes robust error handling for:
- Invalid date formats
- Network connection issues
- API errors
- File system errors
- Invalid ZIP files
- **NEW**: XML parsing errors
- **NEW**: Encoding issues
- **NEW**: File permission errors
- **NEW**: Chunk download failures (continues with remaining chunks)
- **NEW**: Rate limiting (429 errors) with automatic retry
- **NEW**: Service unavailable (503 errors) with automatic retry
- **NEW**: Timeout errors with retry logic
- **NEW**: Invalid market run validation

## Date Format Support

The tool accepts dates in various formats:
- `YYYY-MM-DD` (e.g., `2023-09-19`)
- `YYYY-MM-DD HH:MM` (e.g., `2023-09-19 07:00`)
- `YYYY-MM-DD HH:MM:SS` (e.g., `2023-09-19 07:00:00`)

All dates are converted to UTC timezone format required by the CAISO API.

## Notes

- The CAISO OASIS API provides data in UTC timezone
- System demand data represents forecast data for different time horizons
- Data availability may vary depending on the requested date range and market run
- Large date ranges are automatically chunked to avoid download errors
- The tool automatically creates output directories if they don't exist
- **NEW**: CSV files are automatically generated unless `--no-parse` is used
- **NEW**: Existing CSV files are replaced when new data is downloaded
- **NEW**: Chunked downloads provide better reliability for large datasets
- **NEW**: Rate limiting prevents API throttling and improves success rates
- **NEW**: XML data is automatically converted to CSV format for easy analysis
- **NEW**: Different market runs provide different forecast horizons

## Troubleshooting

1. **Download fails**: Check your internet connection and verify the date range is valid
2. **Invalid date format**: Use the format `YYYY-MM-DD` or `YYYY-MM-DD HH:MM`
3. **File not found**: Ensure the config file exists or the tool will use default values
4. **Permission errors**: Check write permissions for the output directory
5. **XML parsing errors**: The tool will try multiple parsing strategies and show detailed logs
6. **ZIP extraction fails**: Ensure the downloaded file is a valid ZIP archive
7. **Chunk download failures**: The tool will continue with remaining chunks and report success/failure counts
8. **Rate limiting (429 errors)**: The tool automatically retries with exponential backoff
9. **Service unavailable (503 errors)**: The tool automatically retries after delays
10. **Slow downloads**: Increase `rate_limit_delay` in config.ini for more conservative rate limiting
11. **No data extracted**: Check the logs for XML structure information and adjust parsing if needed
12. **Invalid market run**: Use one of the valid options: DA, 2DA, or 7DA

## License

This tool is provided as-is for educational and research purposes. Please ensure compliance with CAISO OASIS terms of service when using this tool. 