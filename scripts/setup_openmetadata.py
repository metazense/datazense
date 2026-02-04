"""
Configure OpenMetadata with PostgreSQL connection and run ingestion.
"""

import requests
import json
import time
import base64

# OpenMetadata API
OM_API_URL = "http://localhost:8585/api/v1"

# PostgreSQL connection details (inside Docker network)
PG_CONFIG = {
    "host": "nyc-taxi-postgres",  # Docker container name
    "port": 5432,
    "username": "taxi_user",
    "password": "taxi_password",
    "database": "nyc_taxi"
}


def get_auth_token():
    """Get JWT token for admin user."""
    # For basic auth, password must be Base64 encoded
    login_url = f"{OM_API_URL}/users/login"
    password_b64 = base64.b64encode("admin".encode()).decode()
    payload = {
        "email": "admin@open-metadata.org",
        "password": password_b64
    }
    try:
        response = requests.post(login_url, json=payload)
        if response.status_code == 200:
            token_data = response.json()
            return token_data.get("accessToken")
        else:
            print(f"  Login failed: {response.status_code} - {response.text[:200]}")
    except Exception as e:
        print(f"  Login error: {e}")
    return None


def create_database_service(headers):
    """Create a PostgreSQL database service in OpenMetadata."""
    print("Creating PostgreSQL database service...")

    service_url = f"{OM_API_URL}/services/databaseServices"

    service_payload = {
        "name": "nyc_taxi_postgres",
        "displayName": "NYC Taxi PostgreSQL",
        "description": "PostgreSQL database containing NYC Yellow Taxi trip data",
        "serviceType": "Postgres",
        "connection": {
            "config": {
                "type": "Postgres",
                "username": PG_CONFIG["username"],
                "authType": {
                    "password": PG_CONFIG["password"]
                },
                "hostPort": f"{PG_CONFIG['host']}:{PG_CONFIG['port']}",
                "database": PG_CONFIG["database"]
            }
        }
    }

    response = requests.post(service_url, headers=headers, json=service_payload)

    if response.status_code == 201:
        print("  Database service created successfully!")
        return response.json()
    elif response.status_code == 409:
        print("  Database service already exists, fetching...")
        get_response = requests.get(f"{service_url}/name/nyc_taxi_postgres", headers=headers)
        return get_response.json()
    else:
        print(f"  Failed to create service: {response.status_code}")
        print(f"  Response: {response.text}")
        return None


def run_ingestion(headers, service_id):
    """Run metadata ingestion for the database service."""
    print("Setting up and running metadata ingestion...")

    ingestion_url = f"{OM_API_URL}/services/ingestionPipelines"

    ingestion_payload = {
        "name": "nyc_taxi_metadata_ingestion",
        "displayName": "NYC Taxi Metadata Ingestion",
        "pipelineType": "metadata",
        "service": {
            "id": service_id,
            "type": "databaseService"
        },
        "sourceConfig": {
            "config": {
                "type": "DatabaseMetadata",
                "schemaFilterPattern": {
                    "includes": ["public"]
                },
                "includeViews": True,
                "includeTables": True,
                "includeStoredProcedures": False,
                "queryLogDuration": 0,
                "useFqnForFiltering": False
            }
        },
        "airflowConfig": {
            "scheduleInterval": None  # Manual run only
        }
    }

    # Create ingestion pipeline
    response = requests.post(ingestion_url, headers=headers, json=ingestion_payload)

    if response.status_code == 201:
        pipeline = response.json()
        print(f"  Ingestion pipeline created: {pipeline['name']}")
        return pipeline
    elif response.status_code == 409:
        print("  Ingestion pipeline already exists")
        get_response = requests.get(f"{ingestion_url}/name/nyc_taxi_postgres.nyc_taxi_metadata_ingestion", headers=headers)
        return get_response.json()
    else:
        print(f"  Failed to create ingestion: {response.status_code}")
        print(f"  Response: {response.text}")
        return None


def trigger_ingestion(headers, pipeline_id):
    """Trigger the ingestion pipeline."""
    print("Triggering ingestion...")

    trigger_url = f"{OM_API_URL}/services/ingestionPipelines/trigger/{pipeline_id}"
    response = requests.post(trigger_url, headers=headers)

    if response.status_code == 200:
        print("  Ingestion triggered successfully!")
        return True
    else:
        print(f"  Failed to trigger: {response.status_code}")
        print(f"  Response: {response.text}")
        return False


def check_tables(headers):
    """Check if tables were discovered."""
    print("\nChecking discovered tables...")

    tables_url = f"{OM_API_URL}/tables"
    params = {"limit": 100}

    response = requests.get(tables_url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        tables = data.get("data", [])
        print(f"  Found {len(tables)} tables:")
        for table in tables:
            print(f"    - {table['fullyQualifiedName']}")
        return tables
    else:
        print(f"  Failed to fetch tables: {response.status_code}")
        return []


def main():
    print("=" * 60)
    print("OpenMetadata Setup - NYC Taxi PostgreSQL")
    print("=" * 60)

    # Check if OpenMetadata is ready
    print("\nChecking OpenMetadata availability...")
    try:
        response = requests.get(f"{OM_API_URL}/system/version")
        if response.status_code != 200:
            print("  OpenMetadata is not ready. Please wait and try again.")
            return
        version = response.json().get("version")
        print(f"  OpenMetadata v{version} is ready!")
    except Exception as e:
        print(f"  Cannot connect to OpenMetadata: {e}")
        return

    # Get auth token
    print("\nAuthenticating...")
    token = get_auth_token()
    if not token:
        print("  Using no-auth mode (token not required)")
        headers = {"Content-Type": "application/json"}
    else:
        print("  Authenticated successfully!")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }

    # Create database service
    print()
    service = create_database_service(headers)
    if not service:
        print("Failed to create database service. Exiting.")
        return

    service_id = service.get("id")
    print(f"  Service ID: {service_id}")

    # Note: OpenMetadata 1.4.0 uses Airflow for ingestion pipelines
    # For local setup without Airflow, we can use the Python SDK directly
    print("\n" + "=" * 60)
    print("Database service configured!")
    print()
    print("To complete ingestion, open the OpenMetadata UI:")
    print("  http://localhost:8585")
    print()
    print("Login with:")
    print("  Email: admin@open-metadata.org")
    print("  Password: admin")
    print()
    print("Then navigate to:")
    print("  Settings > Services > Databases > nyc_taxi_postgres")
    print("  Click 'Add Ingestion' to run metadata discovery")
    print("=" * 60)


if __name__ == "__main__":
    main()
