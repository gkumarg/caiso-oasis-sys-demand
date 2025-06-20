@echo off
echo CAISO OASIS System Demand Downloader - Windows Batch Examples
echo ================================================================

echo.
echo 1. Downloading and extracting to CSV (default: 2DA)...
python caiso_downloader.py

echo.
echo 2. Downloading DA (Day Ahead) data...
python caiso_downloader.py --market-run DA --start-date 2023-09-19 --end-date 2023-09-20

echo.
echo 3. Downloading 2DA (2-Day Ahead) data with chunking...
python caiso_downloader.py --market-run 2DA --start-date 2023-09-19 --end-date 2023-10-20

echo.
echo 4. Downloading 7DA (7-Day Ahead) data...
python caiso_downloader.py --market-run 7DA --start-date 2023-09-19 --end-date 2023-09-20

echo.
echo 5. Downloading with custom directories...
python caiso_downloader.py --output-dir ./my_downloads --data-dir ./my_data

echo.
echo 6. Downloading ZIP only (no XML extraction) with large date range...
python caiso_downloader.py --no-parse --start-date 2023-09-01 --end-date 2023-12-01

echo.
echo 7. Showing information about available data...
python caiso_downloader.py --info

echo.
echo Examples completed!
pause 