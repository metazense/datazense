"""
Download NYC Taxi data for the DataZense project.

Downloads:
- Yellow taxi trip data (1 month)
- Taxi zone lookup CSV
"""

import urllib.request
import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# NYC TLC data URLs
TAXI_DATA_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet"
ZONES_URL = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"

def download_file(url: str, destination: Path, description: str):
    """Download a file with progress indication."""
    print(f"Downloading {description}...")
    print(f"  URL: {url}")
    print(f"  Destination: {destination}")

    if destination.exists():
        print(f"  File already exists, skipping.")
        return

    # Create directory if needed
    destination.parent.mkdir(parents=True, exist_ok=True)

    # Download with progress
    def report_progress(block_num, block_size, total_size):
        downloaded = block_num * block_size
        if total_size > 0:
            percent = min(100, downloaded * 100 / total_size)
            mb_downloaded = downloaded / (1024 * 1024)
            mb_total = total_size / (1024 * 1024)
            print(f"\r  Progress: {percent:.1f}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)", end="", flush=True)

    urllib.request.urlretrieve(url, destination, reporthook=report_progress)
    print(f"\n  Done!")

def main():
    print("=" * 60)
    print("NYC Taxi Data Downloader")
    print("=" * 60)

    # Download taxi trip data
    download_file(
        TAXI_DATA_URL,
        DATA_DIR / "yellow_tripdata_2024-01.parquet",
        "Yellow Taxi Trip Data (January 2024)"
    )

    # Download zone lookup
    download_file(
        ZONES_URL,
        DATA_DIR / "taxi_zone_lookup.csv",
        "Taxi Zone Lookup"
    )

    print("\n" + "=" * 60)
    print("Download complete!")
    print(f"Data saved to: {DATA_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    main()
