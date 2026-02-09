"""
Download pre-generated Synthea CSV data for the healthcare dataset.

Synthea generates realistic (but synthetic) patient data including
encounters, conditions, medications, procedures, etc.

We use pre-generated CSVs rather than requiring Java to run Synthea.
"""

import os
import sys
import zipfile
import shutil
from pathlib import Path
from urllib.request import urlretrieve
from urllib.error import URLError


DATA_DIR = Path(__file__).parent.parent / "data" / "healthcare"

# Pre-generated Synthea samples (public GitHub releases)
DOWNLOAD_URLS = [
    # Synthea sample data from the official Synthea project
    "https://synthetichealth.github.io/synthea-sample-data/downloads/latest/synthea_sample_data_csv_latest.zip",
    # Fallback: smaller sample from Synthea releases
    "https://github.com/synthetichealth/synthea-sample-data/raw/master/downloads/synthea_sample_data_csv_apr2020.zip",
]

# Files we need from the Synthea output
REQUIRED_FILES = [
    "patients.csv",
    "encounters.csv",
    "conditions.csv",
    "medications.csv",
    "procedures.csv",
    "organizations.csv",
    "providers.csv",
    "payers.csv",
]


def download_file(url: str, dest: Path) -> bool:
    """Download a file from URL to destination."""
    print(f"  Downloading from: {url}")
    print(f"  Destination: {dest}")
    try:
        urlretrieve(url, str(dest))
        return True
    except URLError as e:
        print(f"  Failed: {e}")
        return False
    except Exception as e:
        print(f"  Failed: {e}")
        return False


def extract_zip(zip_path: Path, extract_to: Path) -> bool:
    """Extract CSV files from zip, handling nested directories."""
    print(f"  Extracting: {zip_path}")
    try:
        with zipfile.ZipFile(str(zip_path), "r") as zf:
            # Find CSV files in the archive
            csv_files = [f for f in zf.namelist() if f.endswith(".csv")]
            print(f"  Found {len(csv_files)} CSV files in archive")

            for csv_file in csv_files:
                filename = os.path.basename(csv_file)
                if filename in REQUIRED_FILES:
                    # Extract to flat directory
                    source = zf.open(csv_file)
                    target = extract_to / filename
                    with open(str(target), "wb") as f:
                        shutil.copyfileobj(source, f)
                    print(f"  Extracted: {filename}")

        return True
    except zipfile.BadZipFile:
        print(f"  Error: Bad zip file")
        return False
    except Exception as e:
        print(f"  Error extracting: {e}")
        return False


def check_existing_data() -> bool:
    """Check if data already exists."""
    if not DATA_DIR.exists():
        return False
    existing = [f.name for f in DATA_DIR.glob("*.csv")]
    missing = [f for f in REQUIRED_FILES if f not in existing]
    if not missing:
        print("All required CSV files already exist!")
        return True
    if existing:
        print(f"Some files exist but missing: {missing}")
    return False


def main():
    print("=" * 70)
    print("HEALTHCARE DATA DOWNLOAD (Synthea)")
    print("=" * 70)

    # Check if already downloaded
    if check_existing_data():
        print("\nData already available. To re-download, delete data/healthcare/")
        return

    # Create data directory
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = DATA_DIR / "synthea_data.zip"

    # Try each download URL
    downloaded = False
    for url in DOWNLOAD_URLS:
        print(f"\nAttempting download...")
        if download_file(url, zip_path):
            downloaded = True
            break

    if not downloaded:
        print("\n" + "=" * 70)
        print("AUTOMATIC DOWNLOAD FAILED")
        print("=" * 70)
        print("\nPlease download Synthea sample data manually:")
        print("1. Go to: https://synthea.mitre.org/downloads")
        print("2. Download CSV format sample data")
        print(f"3. Extract CSV files to: {DATA_DIR}")
        print(f"\nRequired files: {', '.join(REQUIRED_FILES)}")
        print("\nAlternatively, generate data with Synthea:")
        print("  java -jar synthea-with-dependencies.jar -p 1000 --exporter.csv.export true")
        sys.exit(1)

    # Extract
    print(f"\nExtracting CSV files...")
    if not extract_zip(zip_path, DATA_DIR):
        print("Extraction failed!")
        sys.exit(1)

    # Clean up zip
    zip_path.unlink(missing_ok=True)

    # Verify
    print(f"\nVerifying files...")
    existing = [f.name for f in DATA_DIR.glob("*.csv")]
    missing = [f for f in REQUIRED_FILES if f not in existing]

    if missing:
        print(f"WARNING: Missing files: {missing}")
        print("The dataset may be incomplete. You can still load available data.")
    else:
        print("All required files present!")

    # Show file sizes
    print(f"\nFile sizes:")
    for f in sorted(DATA_DIR.glob("*.csv")):
        size_mb = f.stat().st_size / (1024 * 1024)
        print(f"  {f.name}: {size_mb:.1f} MB")

    print(f"\n" + "=" * 70)
    print("DOWNLOAD COMPLETE")
    print("=" * 70)
    print(f"\nNext step: python scripts/load_healthcare_data.py")


if __name__ == "__main__":
    main()
