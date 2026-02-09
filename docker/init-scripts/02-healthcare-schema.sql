-- Healthcare Database Schema (Synthea synthetic patient data)
-- Creates a separate database in the same PostgreSQL container

-- Create the healthcare database
CREATE DATABASE healthcare;

-- Connect and create schema
\connect healthcare;

-- Grant privileges to taxi_user so the same credentials work
GRANT ALL PRIVILEGES ON DATABASE healthcare TO taxi_user;

-- Organizations (hospitals, clinics)
CREATE TABLE organizations (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    address VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(10),
    zip VARCHAR(10),
    phone VARCHAR(20),
    revenue DECIMAL(15,2),
    utilization DECIMAL(5,2)
);

-- Payers (insurance companies)
CREATE TABLE payers (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    amount_covered DECIMAL(15,2) DEFAULT 0,
    amount_uncovered DECIMAL(15,2) DEFAULT 0,
    revenue DECIMAL(15,2) DEFAULT 0,
    covered_encounters INTEGER DEFAULT 0,
    uncovered_encounters INTEGER DEFAULT 0,
    covered_medications INTEGER DEFAULT 0,
    uncovered_medications INTEGER DEFAULT 0,
    covered_procedures INTEGER DEFAULT 0,
    uncovered_procedures INTEGER DEFAULT 0,
    covered_immunizations INTEGER DEFAULT 0,
    uncovered_immunizations INTEGER DEFAULT 0,
    unique_customers INTEGER DEFAULT 0,
    qols_avg DECIMAL(5,2) DEFAULT 0,
    member_months INTEGER DEFAULT 0
);

-- Patients
CREATE TABLE patients (
    id UUID PRIMARY KEY,
    birth_date DATE,
    death_date DATE,
    ssn VARCHAR(20),
    drivers VARCHAR(20),
    passport VARCHAR(20),
    prefix VARCHAR(10),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    suffix VARCHAR(10),
    maiden VARCHAR(100),
    marital VARCHAR(5),
    race VARCHAR(50),
    ethnicity VARCHAR(50),
    gender VARCHAR(5),
    birthplace VARCHAR(255),
    address VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(10),
    county VARCHAR(100),
    fips VARCHAR(10),
    zip VARCHAR(10),
    lat DECIMAL(10,6),
    lon DECIMAL(10,6),
    healthcare_expenses DECIMAL(15,2) DEFAULT 0,
    healthcare_coverage DECIMAL(15,2) DEFAULT 0,
    income INTEGER DEFAULT 0
);

-- Providers (doctors)
CREATE TABLE providers (
    id UUID PRIMARY KEY,
    organization_id UUID REFERENCES organizations(id),
    name VARCHAR(255),
    gender VARCHAR(5),
    speciality VARCHAR(100),
    address VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(10),
    zip VARCHAR(10),
    lat DECIMAL(10,6),
    lon DECIMAL(10,6),
    encounters INTEGER DEFAULT 0,
    procedures INTEGER DEFAULT 0
);

-- Encounters (visits - fact table)
CREATE TABLE encounters (
    id UUID PRIMARY KEY,
    start_time TIMESTAMP NOT NULL,
    stop_time TIMESTAMP,
    patient_id UUID REFERENCES patients(id),
    organization_id UUID REFERENCES organizations(id),
    provider_id UUID REFERENCES providers(id),
    payer_id UUID REFERENCES payers(id),
    encounter_class VARCHAR(50),
    code VARCHAR(20),
    description VARCHAR(500),
    base_encounter_cost DECIMAL(15,2) DEFAULT 0,
    total_claim_cost DECIMAL(15,2) DEFAULT 0,
    payer_coverage DECIMAL(15,2) DEFAULT 0,
    reason_code VARCHAR(20),
    reason_description VARCHAR(500)
);

-- Conditions (diagnoses)
CREATE TABLE conditions (
    start_date DATE,
    stop_date DATE,
    patient_id UUID REFERENCES patients(id),
    encounter_id UUID REFERENCES encounters(id),
    code VARCHAR(20),
    description VARCHAR(500)
);

-- Medications
CREATE TABLE medications (
    start_date DATE,
    stop_date DATE,
    patient_id UUID REFERENCES patients(id),
    payer_id UUID REFERENCES payers(id),
    encounter_id UUID REFERENCES encounters(id),
    code VARCHAR(20),
    description VARCHAR(500),
    base_cost DECIMAL(15,2) DEFAULT 0,
    payer_coverage DECIMAL(15,2) DEFAULT 0,
    dispenses INTEGER DEFAULT 0,
    total_cost DECIMAL(15,2) DEFAULT 0,
    reason_code VARCHAR(20),
    reason_description VARCHAR(500)
);

-- Procedures
CREATE TABLE procedures (
    start_time TIMESTAMP,
    stop_time TIMESTAMP,
    patient_id UUID REFERENCES patients(id),
    encounter_id UUID REFERENCES encounters(id),
    code VARCHAR(20),
    description VARCHAR(500),
    base_cost DECIMAL(15,2) DEFAULT 0,
    reason_code VARCHAR(20),
    reason_description VARCHAR(500)
);

-- Indexes for common query patterns
CREATE INDEX idx_encounters_patient_id ON encounters(patient_id);
CREATE INDEX idx_encounters_organization_id ON encounters(organization_id);
CREATE INDEX idx_encounters_payer_id ON encounters(payer_id);
CREATE INDEX idx_encounters_class ON encounters(encounter_class);
CREATE INDEX idx_encounters_code ON encounters(code);
CREATE INDEX idx_encounters_start_time ON encounters(start_time);

CREATE INDEX idx_conditions_patient_id ON conditions(patient_id);
CREATE INDEX idx_conditions_encounter_id ON conditions(encounter_id);
CREATE INDEX idx_conditions_code ON conditions(code);

CREATE INDEX idx_medications_patient_id ON medications(patient_id);
CREATE INDEX idx_medications_encounter_id ON medications(encounter_id);
CREATE INDEX idx_medications_code ON medications(code);

CREATE INDEX idx_procedures_patient_id ON procedures(patient_id);
CREATE INDEX idx_procedures_encounter_id ON procedures(encounter_id);
CREATE INDEX idx_procedures_code ON procedures(code);

CREATE INDEX idx_providers_organization_id ON providers(organization_id);

-- Grant all privileges on tables to taxi_user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO taxi_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO taxi_user;

COMMENT ON TABLE patients IS 'Synthetic patient demographics from Synthea';
COMMENT ON TABLE encounters IS 'Healthcare encounters (visits) - primary fact table';
COMMENT ON TABLE conditions IS 'Patient diagnoses with SNOMED CT codes';
COMMENT ON TABLE medications IS 'Prescribed medications with RxNorm codes';
COMMENT ON TABLE procedures IS 'Medical procedures performed';
COMMENT ON TABLE organizations IS 'Healthcare organizations (hospitals, clinics)';
COMMENT ON TABLE providers IS 'Healthcare providers (doctors)';
COMMENT ON TABLE payers IS 'Insurance payers';
