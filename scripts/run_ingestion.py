"""
Run metadata ingestion directly using OpenMetadata Python SDK.
"""

import requests
import base64
import json

OM_API_URL = "http://localhost:8585/api/v1"

# PostgreSQL connection details
PG_CONFIG = {
    "host": "127.0.0.1",
    "port": 5433,
    "username": "taxi_user",
    "password": "taxi_password",
    "database": "nyc_taxi"
}


def get_auth_token():
    """Get JWT token for admin user."""
    login_url = f"{OM_API_URL}/users/login"
    password_b64 = base64.b64encode("admin".encode()).decode()
    payload = {"email": "admin@open-metadata.org", "password": password_b64}
    response = requests.post(login_url, json=payload)
    if response.status_code == 200:
        return response.json().get("accessToken")
    return None


def get_bot_token(headers):
    """Get the ingestion-bot JWT token."""
    bot_url = f"{OM_API_URL}/bots/name/ingestion-bot"
    response = requests.get(bot_url, headers=headers)
    if response.status_code == 200:
        bot_data = response.json()
        bot_user = bot_data.get("botUser", {})
        # Get auth mechanism
        auth_url = f"{OM_API_URL}/users/auth-mechanism/{bot_user.get('id')}"
        auth_response = requests.get(auth_url, headers=headers)
        if auth_response.status_code == 200:
            auth_data = auth_response.json()
            return auth_data.get("config", {}).get("JWTToken")
    return None


def main():
    print("=" * 60)
    print("OpenMetadata Direct Ingestion")
    print("=" * 60)

    # Authenticate
    print("\nAuthenticating...")
    token = get_auth_token()
    if not token:
        print("Failed to authenticate")
        return

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    print("  Authenticated!")

    # Get bot token for ingestion
    print("\nGetting ingestion bot token...")
    bot_token = get_bot_token(headers)
    if bot_token:
        print(f"  Bot token retrieved (length: {len(bot_token)})")
    else:
        print("  Could not get bot token")

    # Try to use metadata-rest to directly register tables
    print("\nRegistering tables via REST API...")

    # Connect to PostgreSQL and get table metadata
    try:
        from sqlalchemy import create_engine, inspect

        db_url = f"postgresql://{PG_CONFIG['username']}:{PG_CONFIG['password']}@{PG_CONFIG['host']}:{PG_CONFIG['port']}/{PG_CONFIG['database']}"
        engine = create_engine(db_url)
        inspector = inspect(engine)

        # Get tables
        tables = inspector.get_table_names(schema='public')
        print(f"  Found tables: {tables}")

        # Get database info
        db_service_url = f"{OM_API_URL}/services/databaseServices/name/nyc_taxi_postgres"
        service = requests.get(db_service_url, headers=headers).json()
        service_fqn = service.get("fullyQualifiedName")

        # Create database entity
        db_url_api = f"{OM_API_URL}/databases"
        db_payload = {
            "name": "nyc_taxi",
            "displayName": "NYC Taxi Database",
            "service": service_fqn
        }
        response = requests.post(db_url_api, headers=headers, json=db_payload)
        if response.status_code == 201:
            print("  Database entity created")
            db_entity = response.json()
        elif response.status_code == 409:
            print("  Database entity already exists")
            db_entity = requests.get(f"{db_url_api}/name/{service_fqn}.nyc_taxi", headers=headers).json()
        else:
            print(f"  Failed to create database: {response.status_code} - {response.text[:200]}")
            return

        # Create schema entity
        schema_url = f"{OM_API_URL}/databaseSchemas"
        schema_payload = {
            "name": "public",
            "displayName": "Public Schema",
            "database": db_entity.get("fullyQualifiedName")
        }
        response = requests.post(schema_url, headers=headers, json=schema_payload)
        if response.status_code == 201:
            print("  Schema entity created")
            schema_entity = response.json()
        elif response.status_code == 409:
            print("  Schema entity already exists")
            schema_entity = requests.get(f"{schema_url}/name/{db_entity.get('fullyQualifiedName')}.public", headers=headers).json()
        else:
            print(f"  Failed to create schema: {response.status_code} - {response.text[:200]}")
            return

        schema_fqn = schema_entity.get("fullyQualifiedName")

        # Create table entities with columns
        tables_url = f"{OM_API_URL}/tables"

        for table_name in tables:
            print(f"\n  Processing table: {table_name}")

            # Get columns
            columns = inspector.get_columns(table_name, schema='public')
            column_list = []
            for col in columns:
                col_type = str(col['type'])
                # Map SQLAlchemy types to OpenMetadata types
                if 'INT' in col_type.upper():
                    om_type = 'INT'
                elif 'VARCHAR' in col_type.upper() or 'TEXT' in col_type.upper() or 'CHAR' in col_type.upper():
                    om_type = 'VARCHAR'
                elif 'TIMESTAMP' in col_type.upper():
                    om_type = 'TIMESTAMP'
                elif 'NUMERIC' in col_type.upper() or 'DECIMAL' in col_type.upper() or 'DOUBLE' in col_type.upper() or 'FLOAT' in col_type.upper():
                    om_type = 'DOUBLE'
                elif 'BOOL' in col_type.upper():
                    om_type = 'BOOLEAN'
                else:
                    om_type = 'VARCHAR'

                col_entry = {
                    "name": col['name'],
                    "dataType": om_type,
                    "dataTypeDisplay": col_type,
                    "description": f"Column {col['name']}"
                }
                # Add dataLength for VARCHAR types
                if om_type == 'VARCHAR':
                    col_entry["dataLength"] = 255
                column_list.append(col_entry)

            # Get primary key
            pk = inspector.get_pk_constraint(table_name, schema='public')
            pk_columns = pk.get('constrained_columns', [])

            # Get row count
            with engine.connect() as conn:
                from sqlalchemy import text
                result = conn.execute(text(f"SELECT COUNT(*) FROM public.{table_name}"))
                row_count = result.scalar()

            table_payload = {
                "name": table_name,
                "displayName": table_name.replace('_', ' ').title(),
                "tableType": "Regular",
                "databaseSchema": schema_fqn,
                "columns": column_list
            }

            response = requests.post(tables_url, headers=headers, json=table_payload)
            if response.status_code == 201:
                print(f"    Created table with {len(column_list)} columns")
                table_entity = response.json()
            elif response.status_code == 409:
                print(f"    Table already exists")
                table_entity = requests.get(f"{tables_url}/name/{schema_fqn}.{table_name}", headers=headers).json()
            else:
                print(f"    Failed: {response.status_code} - {response.text[:200]}")
                continue

            # Update table with profile data (row count)
            table_fqn = table_entity.get("fullyQualifiedName")
            profile_url = f"{OM_API_URL}/tables/{table_entity.get('id')}/tableProfile"
            profile_payload = {
                "timestamp": int(__import__('time').time() * 1000),
                "rowCount": row_count
            }
            requests.put(profile_url, headers=headers, json=profile_payload)
            print(f"    Row count: {row_count:,}")

        print("\n" + "=" * 60)
        print("Ingestion complete!")
        print("\nView in OpenMetadata UI:")
        print("  http://localhost:8585/database/nyc_taxi_postgres.nyc_taxi.public")
        print("=" * 60)

    except ImportError as e:
        print(f"  Error: {e}")
        print("  Please install: uv pip install sqlalchemy psycopg2-binary")
    except Exception as e:
        print(f"  Error: {e}")


if __name__ == "__main__":
    main()
