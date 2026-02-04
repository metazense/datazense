-- NYC Taxi Database Schema
-- This schema supports the Intelligent Semantic Layer project

-- Payment types lookup table
CREATE TABLE payment_types (
    payment_type_id SMALLINT PRIMARY KEY,
    description VARCHAR(50) NOT NULL
);

INSERT INTO payment_types (payment_type_id, description) VALUES
    (1, 'Credit card'),
    (2, 'Cash'),
    (3, 'No charge'),
    (4, 'Dispute'),
    (5, 'Unknown'),
    (6, 'Voided trip');

-- Rate codes lookup table
CREATE TABLE rate_codes (
    rate_code_id SMALLINT PRIMARY KEY,
    description VARCHAR(50) NOT NULL
);

INSERT INTO rate_codes (rate_code_id, description) VALUES
    (1, 'Standard rate'),
    (2, 'JFK'),
    (3, 'Newark'),
    (4, 'Nassau or Westchester'),
    (5, 'Negotiated fare'),
    (6, 'Group ride');

-- Taxi zones lookup table (will be populated from CSV)
CREATE TABLE zones (
    location_id INTEGER PRIMARY KEY,
    borough VARCHAR(50),
    zone_name VARCHAR(100),
    service_zone VARCHAR(50)
);

-- Main trips fact table
CREATE TABLE trips (
    trip_id SERIAL PRIMARY KEY,
    vendor_id SMALLINT,
    pickup_datetime TIMESTAMP NOT NULL,
    dropoff_datetime TIMESTAMP NOT NULL,
    passenger_count SMALLINT,
    trip_distance DECIMAL(10,2),
    pickup_location_id INTEGER REFERENCES zones(location_id),
    dropoff_location_id INTEGER REFERENCES zones(location_id),
    rate_code_id SMALLINT REFERENCES rate_codes(rate_code_id),
    store_and_fwd_flag CHAR(1),
    payment_type SMALLINT REFERENCES payment_types(payment_type_id),
    fare_amount DECIMAL(10,2),
    extra DECIMAL(10,2),
    mta_tax DECIMAL(10,2),
    tip_amount DECIMAL(10,2),
    tolls_amount DECIMAL(10,2),
    improvement_surcharge DECIMAL(10,2),
    total_amount DECIMAL(10,2),
    congestion_surcharge DECIMAL(10,2),
    airport_fee DECIMAL(10,2)
);

-- Indexes for common query patterns
CREATE INDEX idx_trips_pickup_datetime ON trips(pickup_datetime);
CREATE INDEX idx_trips_pickup_location ON trips(pickup_location_id);
CREATE INDEX idx_trips_dropoff_location ON trips(dropoff_location_id);
CREATE INDEX idx_trips_payment_type ON trips(payment_type);

-- Composite index for time-based zone analysis
CREATE INDEX idx_trips_pickup_datetime_location ON trips(pickup_datetime, pickup_location_id);

COMMENT ON TABLE trips IS 'NYC Yellow Taxi trip records';
COMMENT ON TABLE zones IS 'NYC Taxi zone geographic lookup';
COMMENT ON TABLE payment_types IS 'Payment method descriptions';
COMMENT ON TABLE rate_codes IS 'Rate code descriptions (standard, JFK, Newark, etc.)';
