-- Healthcare Operations Analytics Platform
-- Schema: Star Schema for Hospital Operational Data

-- ─────────────────────────────────────────────
-- Dimension Tables
-- ─────────────────────────────────────────────

CREATE TABLE dim_patients (
    patient_key      SERIAL PRIMARY KEY,
    patient_id       VARCHAR(50)  NOT NULL,          -- business key, UUID format
    first_name       VARCHAR(100) NOT NULL,
    last_name        VARCHAR(100) NOT NULL,
    date_of_birth    DATE         NOT NULL,
    gender           VARCHAR(20)  NOT NULL,
    address          TEXT,
    city             VARCHAR(100),
    state            VARCHAR(2),
    zip_code         VARCHAR(10),
    phone_number     VARCHAR(20),
    insurance_type   VARCHAR(50)  NOT NULL,
    -- SCD Type 2 tracking columns
    valid_from       TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    valid_to         TIMESTAMP    DEFAULT '9999-12-31 23:59:59',
    is_current       BOOLEAN      DEFAULT TRUE,
    record_version   INTEGER      DEFAULT 1,
    created_at       TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE dim_departments (
    department_key  SERIAL PRIMARY KEY,
    department_id   VARCHAR(50)  UNIQUE NOT NULL,
    department_name VARCHAR(100) NOT NULL,
    bed_capacity    INTEGER      NOT NULL,
    created_at      TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE dim_physicians (
    physician_key   SERIAL PRIMARY KEY,
    physician_id    VARCHAR(50)  UNIQUE NOT NULL,
    first_name      VARCHAR(100) NOT NULL,
    last_name       VARCHAR(100) NOT NULL,
    specialty       VARCHAR(100) NOT NULL,
    department_key  INTEGER      REFERENCES dim_departments(department_key),
    created_at      TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

-- ─────────────────────────────────────────────
-- Fact Tables
-- ─────────────────────────────────────────────

CREATE TABLE fact_encounters (
    encounter_key   SERIAL PRIMARY KEY,
    encounter_id    VARCHAR(50)  UNIQUE NOT NULL,
    patient_key     INTEGER      REFERENCES dim_patients(patient_key),
    department_key  INTEGER      REFERENCES dim_departments(department_key),
    physician_key   INTEGER      REFERENCES dim_physicians(physician_key),
    admission_date  TIMESTAMP    NOT NULL,
    discharge_date  TIMESTAMP,
    admission_type  VARCHAR(50)  NOT NULL,
    chief_complaint TEXT,
    created_at      TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE fact_bed_events (
    bed_event_key   SERIAL PRIMARY KEY,
    encounter_key   INTEGER      REFERENCES fact_encounters(encounter_key),
    department_key  INTEGER      REFERENCES dim_departments(department_key),
    bed_number      INTEGER      NOT NULL,
    event_type      VARCHAR(20)  NOT NULL,
    event_timestamp TIMESTAMP    NOT NULL,
    created_at      TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

-- ─────────────────────────────────────────────
-- Indexes
-- ─────────────────────────────────────────────

-- SCD2 indexes for dim_patients
CREATE INDEX idx_patients_business_key_current ON dim_patients(patient_id, is_current);
CREATE INDEX idx_patients_valid_dates          ON dim_patients(valid_from, valid_to);

CREATE INDEX idx_encounters_admission_date  ON fact_encounters(admission_date);
CREATE INDEX idx_encounters_patient_key     ON fact_encounters(patient_key);
CREATE INDEX idx_bed_events_timestamp       ON fact_bed_events(event_timestamp);
CREATE INDEX idx_bed_events_encounter_key   ON fact_bed_events(encounter_key);
