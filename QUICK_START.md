# Quick Start Guide

## Install Dependencies
```bash
pip install -r requirements.txt
```

## Basic Usage

### Download and extract XML to CSV (default: 2DA)
```bash
python caiso_downloader.py
```

### Download different market runs
```bash
# Day Ahead (DA)
python caiso_downloader.py --market-run DA --start-date 2023-09-19 --end-date 2023-09-20

# 2-Day Ahead (2DA) - default
python caiso_downloader.py --market-run 2DA --start-date 2023-09-19 --end-date 2023-10-20

# 7-Day Ahead (7DA)
python caiso_downloader.py --market-run 7DA --start-date 2023-09-19 --end-date 2023-09-20
```

### Download with specific time
```bash
python caiso_downloader.py --start-date "2023-09-19 07:00" --end-date "2023-09-20 07:00"
```

### Download ZIP only (no XML extraction)
```bash
python caiso_downloader.py --no-parse
```

## What You Get

- **Input**: Date range and market run type (from command line or config file)
- **Output**: 
  - 📦 ZIP file(s) containing system demand data (XML files inside)
  - 📊 CSV file(s) with parsed data (extracted from XML)
- **Location**: 
  - ZIP files: `./downloads/` folder (or custom directory)
  - CSV files: `./data/` folder (or custom directory)
- **Filenames**: 
  - `system_demand_{market_run}_{start_date}_{end_date}.zip`
  - `system_demand_{market_run}_{start_date}_{end_date}.csv`
  - For large ranges: `chunk_01_of_03_system_demand_{market_run}_{start_date}_{end_date}.zip`

## Market Run Types

- **DA (Day Ahead)**: Next day forecasts
- **2DA (2-Day Ahead)**: 2-day ahead forecasts (default)
- **7DA (7-Day Ahead)**: 7-day ahead forecasts

## Automatic Chunking

- ✅ **Smart chunking**: Large date ranges (>30 days) are automatically split
- ✅ **Progress tracking**: Shows download progress for each chunk
- ✅ **Error resilience**: Continues downloading if one chunk fails
- ✅ **Clear naming**: Chunked files include chunk information

## Rate Limiting & Retry Logic

- ✅ **API protection**: 5-second delays between requests (configurable)
- ✅ **Automatic retry**: 3 attempts per chunk with exponential backoff
- ✅ **429 error handling**: Automatically retries on "Too Many Requests"
- ✅ **503 error handling**: Automatically retries on service unavailable
- ✅ **Jitter**: Random delays to avoid overwhelming the API

## XML to CSV Features

- ✅ **Automatic extraction**: No manual ZIP extraction needed
- ✅ **XML parsing**: Extracts data from CAISO OASIS XML files
- ✅ **File replacement**: Existing CSV files are automatically removed
- ✅ **Multiple encodings**: Supports UTF-8, Latin-1, CP1252
- ✅ **Data combination**: Combines multiple XML files from ZIP
- ✅ **Data summary**: Shows row count, columns, and data shape
- ✅ **Sample preview**: Shows first 3 rows of extracted data
- ✅ **Separate data directory**: CSV files saved to `./data` by default

## Configuration

Edit `config.ini` to change:
- Default dates
- Output directories (ZIP and CSV)
- File naming format
- XML extraction settings
- Maximum days per chunk (default: 30)
- Rate limiting delay (default: 5 seconds)
- Retry attempts (default: 3)

## Need Help?

```bash
python caiso_downloader.py --help
```

## Test It

Run the example script:
```bash
python example_usage.py
```

Or use the Windows batch file:
```bash
download_example.bat