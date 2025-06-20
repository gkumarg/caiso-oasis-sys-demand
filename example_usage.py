#!/usr/bin/env python3
"""
Example usage of the CAISO OASIS System Demand Downloader

This script demonstrates how to use the downloader programmatically.
"""

from caiso_downloader import CAISODownloader
import os

def main():
    """Example usage of the CAISO downloader."""
    
    print("CAISO OASIS System Demand Downloader - Example Usage")
    print("=" * 60)
    
    # Initialize the downloader
    downloader = CAISODownloader()
    
    # Example 1: Download using config file defaults (2DA, with CSV extraction)
    print("\n1. Downloading using config file defaults (2DA, with CSV extraction)...")
    # This will create files like:
    # - chunk_01_of_01_system_demand_2DA_20230919T0700-0000_20230929T0000-0000.zip
    # - data/system_demand_2DA_20230919T0700_20230929T0000.csv
    result1 = downloader.download_data()
    if result1:
        print(f"✅ Success!")
        print(f"📦 Downloaded {result1['successful_chunks']}/{result1['total_chunks']} chunks for {result1['market_run']}")
        if result1['csv_files']:
            print(f"📊 CSV files created: {len(result1['csv_files'])} files")
    else:
        print("❌ Failed")
    
    # Example 2: Download DA (Day Ahead) data
    print("\n2. Downloading DA (Day Ahead) data...")
    # This will create files like:
    # - chunk_01_of_01_system_demand_DA_20230919T0700-0000_20230920T0700-0000.zip
    # - da_data/system_demand_DA_20230919T0700_20230920T0700.csv
    # Note: DA internally maps to "DAM" (Day Ahead Market) in the CAISO API
    result2 = downloader.download_data(
        start_date="2023-09-19",
        end_date="2023-09-20",
        market_run="DA",
        output_dir="./da_downloads",
        data_dir="./da_data"
    )
    if result2:
        print(f"✅ Success!")
        print(f"📦 Downloaded {result2['successful_chunks']}/{result2['total_chunks']} chunks for {result2['market_run']}")
        if result2['csv_files']:
            print(f"📊 CSV files created: {len(result2['csv_files'])} files")
    else:
        print("❌ Failed")
    
    # Example 3: Download 2DA (2-Day Ahead) data with chunking
    print("\n3. Downloading 2DA (2-Day Ahead) data with chunking...")
    # This will create files like:
    # - chunk_01_of_02_system_demand_2DA_20230919T0700-0000_20231019T0700-0000.zip
    # - chunk_02_of_02_system_demand_2DA_20231019T0700-0000_20231020T0700-0000.zip
    # - 2da_data/system_demand_2DA_20230919T0700_20231019T0700.csv
    # - 2da_data/system_demand_2DA_20231019T0700_20231020T0700.csv
    result3 = downloader.download_data(
        start_date="2023-09-19",
        end_date="2023-10-20",  # This is 31 days, so it will be chunked
        market_run="2DA",
        output_dir="./2da_downloads",
        data_dir="./2da_data"
    )
    if result3:
        print(f"✅ Success!")
        print(f"📦 Downloaded {result3['successful_chunks']}/{result3['total_chunks']} chunks for {result3['market_run']}")
        if result3['csv_files']:
            print(f"📊 CSV files created: {len(result3['csv_files'])} files")
    else:
        print("❌ Failed")
    
    # Example 4: Download 7DA (7-Day Ahead) data with specific time
    print("\n4. Downloading 7DA (7-Day Ahead) data with specific time...")
    # This will create files like:
    # - chunk_01_of_01_system_demand_7DA_20230919T0700-0000_20230920T0700-0000.zip
    # - 7da_data/system_demand_7DA_20230919T0700_20230920T0700.csv
    result4 = downloader.download_data(
        start_date="2023-09-19 07:00",
        end_date="2023-09-20 07:00",
        market_run="7DA",
        output_dir="./7da_downloads",
        data_dir="./7da_data"
    )
    if result4:
        print(f"✅ Success!")
        print(f"📦 Downloaded {result4['successful_chunks']}/{result4['total_chunks']} chunks for {result4['market_run']}")
        if result4['csv_files']:
            print(f"📊 CSV files created: {len(result4['csv_files'])} files")
    else:
        print("❌ Failed")
    
    # Example 5: Download ZIP only (no XML extraction) with large date range
    print("\n5. Downloading ZIP only (no XML extraction) with large date range...")
    result5 = downloader.download_data(
        start_date="2023-09-01",
        end_date="2023-12-01",  # This is 91 days, will be chunked into 4 parts
        market_run="2DA",
        output_dir="./zip_only_downloads",
        data_dir="./zip_only_data",
        extract_and_parse=False
    )
    if result5:
        print(f"✅ Success!")
        print(f"📦 Downloaded {result5['successful_chunks']}/{result5['total_chunks']} chunks for {result5['market_run']}")
        if result5['csv_files']:
            print(f"📊 CSV files created: {len(result5['csv_files'])} files")
        else:
            print("📊 No CSV files created (ZIP only mode)")
    else:
        print("❌ Failed")
    
    # Example 6: Show available data information
    print("\n6. Information about available data:")
    downloader.get_available_dates()
    
    print("\n" + "=" * 60)
    print("Example usage completed!")

if __name__ == "__main__":
    main() 