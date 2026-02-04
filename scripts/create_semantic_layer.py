"""
Create Semantic Layer in OpenMetadata using Glossary.

This script creates:
1. NYC Taxi Business Glossary
2. Metric terms (Trip Revenue, Trip Count, etc.)
3. Dimension terms (Pickup Zone, Borough, etc.)
4. Links terms to table columns
"""

import requests
import base64
import json

OM_API_URL = "http://localhost:8585/api/v1"


def get_auth_headers():
    """Get authenticated headers."""
    password_b64 = base64.b64encode("admin".encode()).decode()
    payload = {"email": "admin@open-metadata.org", "password": password_b64}
    response = requests.post(f"{OM_API_URL}/users/login", json=payload)
    token = response.json().get("accessToken")
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }


def create_glossary(headers):
    """Create the main glossary."""
    print("\n1. Creating NYC Taxi Business Glossary...")

    glossary_url = f"{OM_API_URL}/glossaries"

    payload = {
        "name": "NYCTaxiBusinessGlossary",
        "displayName": "NYC Taxi Business Glossary",
        "description": "Business terms and definitions for NYC Yellow Taxi data. Contains metrics, dimensions, and business concepts used for analytics."
    }

    response = requests.post(glossary_url, headers=headers, json=payload)

    if response.status_code == 201:
        glossary = response.json()
        print(f"   Created glossary: {glossary['name']}")
        return glossary
    elif response.status_code == 409:
        print("   Glossary already exists, fetching...")
        response = requests.get(f"{glossary_url}/name/NYCTaxiBusinessGlossary", headers=headers)
        return response.json()
    else:
        print(f"   Failed: {response.status_code} - {response.text[:200]}")
        return None


def create_glossary_term(headers, glossary_fqn, name, display_name, description, parent_fqn=None, synonyms=None, related_terms=None):
    """Create a glossary term."""
    term_url = f"{OM_API_URL}/glossaryTerms"

    payload = {
        "name": name,
        "displayName": display_name,
        "description": description,
        "glossary": glossary_fqn,
        "synonyms": synonyms or []
    }

    if parent_fqn:
        payload["parent"] = parent_fqn

    response = requests.post(term_url, headers=headers, json=payload)

    if response.status_code == 201:
        term = response.json()
        return term
    elif response.status_code == 409:
        # Already exists, fetch it
        term_fqn = f"{glossary_fqn}.{name}"
        response = requests.get(f"{term_url}/name/{term_fqn}", headers=headers)
        if response.status_code == 200:
            return response.json()

    return None


def create_category_terms(headers, glossary_fqn):
    """Create category terms (Metrics, Dimensions, Business Concepts)."""
    print("\n2. Creating category terms...")

    categories = [
        {
            "name": "Metrics",
            "displayName": "Metrics",
            "description": "Quantitative measures that can be aggregated. These define HOW to calculate business KPIs from raw data."
        },
        {
            "name": "Dimensions",
            "displayName": "Dimensions",
            "description": "Categorical attributes used for grouping and filtering. These define the axes for slicing metrics."
        },
        {
            "name": "BusinessConcepts",
            "displayName": "Business Concepts",
            "description": "Domain-specific terms that provide business context and meaning to the data."
        }
    ]

    created = {}
    for cat in categories:
        term = create_glossary_term(
            headers,
            glossary_fqn,
            cat["name"],
            cat["displayName"],
            cat["description"]
        )
        if term:
            print(f"   Created: {cat['displayName']}")
            created[cat["name"]] = term
        else:
            print(f"   Failed: {cat['displayName']}")

    return created


def create_metric_terms(headers, glossary_fqn, parent_fqn):
    """Create metric definitions."""
    print("\n3. Creating metric terms...")

    metrics = [
        {
            "name": "TripRevenue",
            "displayName": "Trip Revenue",
            "description": "**Definition:** Total earnings from a single taxi trip.\n\n**Formula:** `fare_amount + tip_amount`\n\n**Unit:** USD\n\n**Business Context:** Primary revenue metric for driver and fleet performance analysis.",
            "synonyms": ["Revenue", "Trip Earnings", "Total Fare"]
        },
        {
            "name": "TripCount",
            "displayName": "Trip Count",
            "description": "**Definition:** Number of completed taxi trips.\n\n**Formula:** `COUNT(*)`\n\n**Business Context:** Volume metric indicating demand and driver activity levels.",
            "synonyms": ["Number of Trips", "Ride Count", "Trip Volume"]
        },
        {
            "name": "AverageFare",
            "displayName": "Average Fare",
            "description": "**Definition:** Mean fare amount per trip.\n\n**Formula:** `AVG(fare_amount)`\n\n**Unit:** USD\n\n**Business Context:** Indicates typical trip value, useful for pricing analysis.",
            "synonyms": ["Mean Fare", "Avg Fare"]
        },
        {
            "name": "TipPercentage",
            "displayName": "Tip Percentage",
            "description": "**Definition:** Tip amount as percentage of fare.\n\n**Formula:** `(tip_amount / fare_amount) * 100`\n\n**Unit:** Percent\n\n**Business Context:** Indicator of customer satisfaction and service quality. Note: Cash tips are not recorded.",
            "synonyms": ["Tip Rate", "Tip Ratio"]
        },
        {
            "name": "TripDuration",
            "displayName": "Trip Duration",
            "description": "**Definition:** Time elapsed from pickup to dropoff.\n\n**Formula:** `dropoff_datetime - pickup_datetime`\n\n**Unit:** Minutes\n\n**Business Context:** Efficiency metric affecting driver earnings per hour.",
            "synonyms": ["Ride Duration", "Trip Time", "Travel Time"]
        },
        {
            "name": "TripDistance",
            "displayName": "Trip Distance",
            "description": "**Definition:** Total distance traveled during the trip.\n\n**Formula:** Direct from `trip_distance` column\n\n**Unit:** Miles\n\n**Business Context:** Key factor in fare calculation and fuel cost estimation.",
            "synonyms": ["Ride Distance", "Miles Traveled"]
        },
        {
            "name": "TotalAmount",
            "displayName": "Total Amount",
            "description": "**Definition:** Complete charge to the passenger including all fees.\n\n**Formula:** `fare_amount + tip_amount + tolls_amount + mta_tax + improvement_surcharge + congestion_surcharge + airport_fee`\n\n**Unit:** USD\n\n**Business Context:** Total transaction value, includes regulatory fees.",
            "synonyms": ["Total Charge", "Final Amount"]
        }
    ]

    created = []
    for m in metrics:
        term = create_glossary_term(
            headers,
            glossary_fqn,
            m["name"],
            m["displayName"],
            m["description"],
            parent_fqn=parent_fqn,
            synonyms=m.get("synonyms", [])
        )
        if term:
            print(f"   Created: {m['displayName']}")
            created.append(term)

    return created


def create_dimension_terms(headers, glossary_fqn, parent_fqn):
    """Create dimension definitions."""
    print("\n4. Creating dimension terms...")

    dimensions = [
        {
            "name": "PickupZone",
            "displayName": "Pickup Zone",
            "description": "**Definition:** The taxi zone where the trip started.\n\n**Source:** `trips.pickup_location_id` → `zones.zone_name`\n\n**Business Context:** Indicates demand hotspots and trip origin patterns.",
            "synonyms": ["Pickup Location", "Origin Zone", "Start Zone"]
        },
        {
            "name": "DropoffZone",
            "displayName": "Dropoff Zone",
            "description": "**Definition:** The taxi zone where the trip ended.\n\n**Source:** `trips.dropoff_location_id` → `zones.zone_name`\n\n**Business Context:** Indicates destination patterns and potential repositioning needs.",
            "synonyms": ["Dropoff Location", "Destination Zone", "End Zone"]
        },
        {
            "name": "Borough",
            "displayName": "Borough",
            "description": "**Definition:** NYC administrative district (Manhattan, Brooklyn, Queens, Bronx, Staten Island).\n\n**Source:** `zones.borough`\n\n**Business Context:** High-level geographic grouping. Manhattan dominates taxi activity.",
            "synonyms": ["District", "NYC Borough"]
        },
        {
            "name": "PaymentMethod",
            "displayName": "Payment Method",
            "description": "**Definition:** How the passenger paid for the trip.\n\n**Source:** `trips.payment_type` → `payment_types.description`\n\n**Values:**\n- 1 = Credit Card\n- 2 = Cash\n- 3 = No Charge\n- 4 = Dispute\n- 5 = Unknown\n- 6 = Voided\n\n**Business Context:** Credit card payments have recorded tips; cash tips are not captured.",
            "synonyms": ["Payment Type", "Pay Method"]
        },
        {
            "name": "RateType",
            "displayName": "Rate Type",
            "description": "**Definition:** The rate code used for fare calculation.\n\n**Source:** `trips.rate_code_id` → `rate_codes.description`\n\n**Values:**\n- 1 = Standard Rate\n- 2 = JFK Airport\n- 3 = Newark Airport\n- 4 = Nassau/Westchester\n- 5 = Negotiated Fare\n- 6 = Group Ride\n\n**Business Context:** Airport trips (2,3) have flat rates, more predictable revenue.",
            "synonyms": ["Rate Code", "Fare Type"]
        },
        {
            "name": "PickupDate",
            "displayName": "Pickup Date",
            "description": "**Definition:** Calendar date when the trip started.\n\n**Source:** `DATE(trips.pickup_datetime)`\n\n**Business Context:** Used for daily/weekly/monthly trend analysis.",
            "synonyms": ["Trip Date", "Date"]
        },
        {
            "name": "PickupHour",
            "displayName": "Pickup Hour",
            "description": "**Definition:** Hour of day when the trip started (0-23).\n\n**Source:** `HOUR(trips.pickup_datetime)`\n\n**Business Context:** Reveals demand patterns: rush hours, late night, etc.",
            "synonyms": ["Hour of Day", "Time of Day"]
        }
    ]

    created = []
    for d in dimensions:
        term = create_glossary_term(
            headers,
            glossary_fqn,
            d["name"],
            d["displayName"],
            d["description"],
            parent_fqn=parent_fqn,
            synonyms=d.get("synonyms", [])
        )
        if term:
            print(f"   Created: {d['displayName']}")
            created.append(term)

    return created


def create_business_concept_terms(headers, glossary_fqn, parent_fqn):
    """Create business concept definitions."""
    print("\n5. Creating business concept terms...")

    concepts = [
        {
            "name": "AirportTrip",
            "displayName": "Airport Trip",
            "description": "**Definition:** A trip to/from JFK or Newark airport.\n\n**Identification:** `rate_code_id IN (2, 3)`\n\n**Business Context:** Flat-rate fares provide predictable revenue. High-value trips for drivers.",
            "synonyms": ["Airport Ride", "JFK Trip", "Newark Trip"]
        },
        {
            "name": "CashPayment",
            "displayName": "Cash Payment",
            "description": "**Definition:** Trip paid with cash.\n\n**Identification:** `payment_type = 2`\n\n**Business Context:** Cash tips are NOT recorded in the data. Tip analysis should exclude cash trips for accuracy.",
            "synonyms": ["Cash Fare"]
        },
        {
            "name": "PeakHours",
            "displayName": "Peak Hours",
            "description": "**Definition:** High-demand time periods.\n\n**Identification:** Typically 7-9 AM and 5-8 PM on weekdays.\n\n**Business Context:** Higher demand, potential surge pricing, longer trip durations due to traffic.",
            "synonyms": ["Rush Hour", "Busy Hours"]
        },
        {
            "name": "LongDistanceTrip",
            "displayName": "Long Distance Trip",
            "description": "**Definition:** Trips exceeding typical distance.\n\n**Identification:** `trip_distance > 10` miles\n\n**Business Context:** Higher revenue per trip but lower trips per hour for drivers.",
            "synonyms": ["Long Ride", "Extended Trip"]
        }
    ]

    created = []
    for c in concepts:
        term = create_glossary_term(
            headers,
            glossary_fqn,
            c["name"],
            c["displayName"],
            c["description"],
            parent_fqn=parent_fqn,
            synonyms=c.get("synonyms", [])
        )
        if term:
            print(f"   Created: {c['displayName']}")
            created.append(term)

    return created


def add_column_descriptions(headers):
    """Add business descriptions to table columns."""
    print("\n6. Adding column descriptions to tables...")

    # Column descriptions for trips table
    trips_columns = {
        "vendor_id": "Identifies the taxi technology provider (1=CMT, 2=VeriFone)",
        "pickup_datetime": "Date and time when the meter was engaged at pickup",
        "dropoff_datetime": "Date and time when the meter was disengaged at dropoff",
        "passenger_count": "Number of passengers in the vehicle (driver-reported)",
        "trip_distance": "Trip distance in miles as reported by the taximeter",
        "pickup_location_id": "TLC Taxi Zone where the trip began (FK to zones)",
        "dropoff_location_id": "TLC Taxi Zone where the trip ended (FK to zones)",
        "rate_code_id": "Fare rate code (1=Standard, 2=JFK, 3=Newark, 4=Nassau, 5=Negotiated, 6=Group)",
        "store_and_fwd_flag": "Whether trip data was held in vehicle memory before sending (Y/N)",
        "payment_type": "Payment method (1=Card, 2=Cash, 3=No charge, 4=Dispute, 5=Unknown, 6=Voided)",
        "fare_amount": "Base fare calculated by the meter based on time and distance",
        "extra": "Miscellaneous extras and surcharges (rush hour, overnight)",
        "mta_tax": "MTA tax automatically triggered based on metered rate",
        "tip_amount": "Tip amount (only for credit card payments, cash tips not recorded)",
        "tolls_amount": "Total amount of all tolls paid during the trip",
        "improvement_surcharge": "Improvement surcharge assessed on hailed trips",
        "total_amount": "Total amount charged to passenger (excludes cash tips)",
        "congestion_surcharge": "Congestion surcharge for trips in Manhattan below 96th St",
        "airport_fee": "Airport pickup/dropoff fee"
    }

    # Get trips table
    table_url = f"{OM_API_URL}/tables/name/nyc_taxi_postgres.nyc_taxi.public.trips"
    response = requests.get(table_url, headers=headers, params={"fields": "columns"})

    if response.status_code != 200:
        print(f"   Failed to fetch trips table: {response.status_code}")
        return

    table = response.json()
    table_id = table.get("id")
    columns = table.get("columns", [])

    # Update each column with description
    updated_columns = []
    for col in columns:
        col_name = col.get("name")
        if col_name in trips_columns:
            col["description"] = trips_columns[col_name]
        updated_columns.append(col)

    # Patch the table with updated columns
    patch_url = f"{OM_API_URL}/tables/{table_id}"
    patch_payload = [
        {
            "op": "replace",
            "path": "/columns",
            "value": updated_columns
        }
    ]

    response = requests.patch(patch_url, headers=headers, json=patch_payload)
    if response.status_code == 200:
        print(f"   Updated {len(trips_columns)} column descriptions in trips table")
    else:
        print(f"   Failed to update columns: {response.status_code} - {response.text[:200]}")

    # Update zones table
    zones_columns = {
        "location_id": "Unique identifier for the taxi zone",
        "borough": "NYC borough name (Manhattan, Brooklyn, Queens, Bronx, Staten Island)",
        "zone_name": "Name of the taxi zone (e.g., 'Upper East Side North')",
        "service_zone": "Service zone category (Yellow Zone, Boro Zone, Airports, etc.)"
    }

    table_url = f"{OM_API_URL}/tables/name/nyc_taxi_postgres.nyc_taxi.public.zones"
    response = requests.get(table_url, headers=headers, params={"fields": "columns"})

    if response.status_code == 200:
        table = response.json()
        table_id = table.get("id")
        columns = table.get("columns", [])

        for col in columns:
            if col.get("name") in zones_columns:
                col["description"] = zones_columns[col.get("name")]

        response = requests.patch(
            f"{OM_API_URL}/tables/{table_id}",
            headers=headers,
            json=[{"op": "replace", "path": "/columns", "value": columns}]
        )
        if response.status_code == 200:
            print(f"   Updated {len(zones_columns)} column descriptions in zones table")


def link_terms_to_assets(headers, glossary_fqn):
    """Link glossary terms to table columns via tags."""
    print("\n7. Linking glossary terms to table columns...")

    # Define mappings: term -> list of column FQNs
    term_to_columns = {
        "Metrics.TripRevenue": [
            "nyc_taxi_postgres.nyc_taxi.public.trips.fare_amount",
            "nyc_taxi_postgres.nyc_taxi.public.trips.tip_amount"
        ],
        "Metrics.TripDistance": [
            "nyc_taxi_postgres.nyc_taxi.public.trips.trip_distance"
        ],
        "Metrics.TripDuration": [
            "nyc_taxi_postgres.nyc_taxi.public.trips.pickup_datetime",
            "nyc_taxi_postgres.nyc_taxi.public.trips.dropoff_datetime"
        ],
        "Metrics.TotalAmount": [
            "nyc_taxi_postgres.nyc_taxi.public.trips.total_amount"
        ],
        "Dimensions.PickupZone": [
            "nyc_taxi_postgres.nyc_taxi.public.trips.pickup_location_id"
        ],
        "Dimensions.DropoffZone": [
            "nyc_taxi_postgres.nyc_taxi.public.trips.dropoff_location_id"
        ],
        "Dimensions.Borough": [
            "nyc_taxi_postgres.nyc_taxi.public.zones.borough"
        ],
        "Dimensions.PaymentMethod": [
            "nyc_taxi_postgres.nyc_taxi.public.trips.payment_type"
        ],
        "Dimensions.RateType": [
            "nyc_taxi_postgres.nyc_taxi.public.trips.rate_code_id"
        ]
    }

    linked_count = 0
    for term_path, column_fqns in term_to_columns.items():
        term_fqn = f"{glossary_fqn}.{term_path}"

        for col_fqn in column_fqns:
            # Get the term to use as tag
            term_url = f"{OM_API_URL}/glossaryTerms/name/{term_fqn}"
            term_response = requests.get(term_url, headers=headers)

            if term_response.status_code != 200:
                continue

            term = term_response.json()
            term_id = term.get("id")

            # Add term as tag to column
            # First get the table
            parts = col_fqn.rsplit(".", 1)
            table_fqn = parts[0]
            col_name = parts[1]

            table_url = f"{OM_API_URL}/tables/name/{table_fqn}"
            table_response = requests.get(table_url, headers=headers, params={"fields": "columns,tags"})

            if table_response.status_code != 200:
                continue

            table = table_response.json()

            # Find the column and add tag
            for col in table.get("columns", []):
                if col.get("name") == col_name:
                    # Add glossary term tag to column
                    tag_url = f"{OM_API_URL}/tables/{table.get('id')}/columns/{col.get('name')}/tags"
                    tag_payload = [
                        {
                            "tagFQN": term_fqn,
                            "source": "Glossary",
                            "labelType": "Manual"
                        }
                    ]

                    response = requests.put(tag_url, headers=headers, json=tag_payload)
                    if response.status_code == 200:
                        linked_count += 1
                    break

    print(f"   Linked {linked_count} term-column associations")


def main():
    print("=" * 60)
    print("Creating Semantic Layer in OpenMetadata")
    print("=" * 60)

    # Authenticate
    print("\nAuthenticating...")
    headers = get_auth_headers()
    print("   Authenticated!")

    # Create glossary
    glossary = create_glossary(headers)
    if not glossary:
        print("Failed to create glossary. Exiting.")
        return

    glossary_fqn = glossary.get("fullyQualifiedName")

    # Create categories
    categories = create_category_terms(headers, glossary_fqn)

    # Create metric terms
    if "Metrics" in categories:
        metrics_fqn = categories["Metrics"].get("fullyQualifiedName")
        create_metric_terms(headers, glossary_fqn, metrics_fqn)

    # Create dimension terms
    if "Dimensions" in categories:
        dims_fqn = categories["Dimensions"].get("fullyQualifiedName")
        create_dimension_terms(headers, glossary_fqn, dims_fqn)

    # Create business concept terms
    if "BusinessConcepts" in categories:
        concepts_fqn = categories["BusinessConcepts"].get("fullyQualifiedName")
        create_business_concept_terms(headers, glossary_fqn, concepts_fqn)

    # Add column descriptions
    add_column_descriptions(headers)

    # Link terms to assets
    link_terms_to_assets(headers, glossary_fqn)

    print("\n" + "=" * 60)
    print("Semantic Layer created successfully!")
    print("\nView in OpenMetadata:")
    print("  Glossary: http://localhost:8585/glossary/NYCTaxiBusinessGlossary")
    print("  Tables:   http://localhost:8585/database/nyc_taxi_postgres.nyc_taxi.public")
    print("=" * 60)


if __name__ == "__main__":
    main()
