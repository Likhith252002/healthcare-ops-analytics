# Healthcare Operations Analytics Platform

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![PostgreSQL](https://img.shields.io/badge/postgresql-15+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

> Production-grade healthcare analytics platform demonstrating data engineering and analytics capabilities using synthetic patient data.

## Overview
Production-grade healthcare analytics platform using synthetic patient data in
HIPAA-compliant development environment. Demonstrates end-to-end data engineering
and analytics capabilities.

## Tech Stack
- **Database**: PostgreSQL 15+
- **Data Generation**: Python, Faker
- **Orchestration**: Apache Airflow (coming soon)
- **Transformation**: dbt (coming soon)
- **Visualization**: Streamlit (coming soon)

## Project Structure
```
healthcare-ops-analytics/
├── sql/              # Database schemas and queries
├── src/              # Python source code
│   ├── generators/   # Data generation scripts
│   └── utils/        # Helper functions
├── config/           # Configuration files
└── logs/             # Application logs
```

## Setup Instructions
1. Install PostgreSQL 15+ locally or via Docker
2. Create database: `createdb healthcare_ops`
3. Copy `.env.example` to `.env` and update credentials
4. Install dependencies: `pip install -r requirements.txt`
5. Run setup (instructions coming in next phase)

## Database Setup
```bash
# Step 1: Create .env file
cp .env.example .env
# Edit .env with your PostgreSQL credentials

# Step 2: Create database
createdb healthcare_ops

# Step 3: Run setup script
python src/setup_database.py
```

Expected output:
```
Starting database setup...
✓ Executed: CREATE TABLE dim_patients...
✓ Executed: CREATE TABLE dim_departments...
✓ Database setup complete!
Tables created: dim_patients, dim_departments, dim_physicians, fact_encounters, fact_bed_events
```

## Analytics Queries

Pre-built SQL queries for operational metrics:
```bash
# ER wait time analysis
psql -d healthcare_ops -f sql/analytics/er_wait_times.sql

# Bed utilization rates
psql -d healthcare_ops -f sql/analytics/bed_utilization.sql

# Length of stay analysis
psql -d healthcare_ops -f sql/analytics/length_of_stay.sql

# Daily volume trends
psql -d healthcare_ops -f sql/analytics/daily_volume.sql
```

See `sql/analytics/README.md` for detailed query documentation.

## Data Generation

### Run Full Pipeline (Recommended)
```bash
python src/main.py
```

Runs all generators in order and prints a final summary:
```
================================================================================
DATA GENERATION SUMMARY
================================================================================
dim_patients: 1,000 records
dim_departments: 6 records
dim_physicians: 50 records
fact_encounters: 5,000 records
fact_bed_events: 10,000 records
================================================================================
Total records: 16,056
Total time: 45.32 seconds
================================================================================
Encounter metrics:
  Simulation period: 90 days
  Total encounters: 5,000
  Average per day: 55.6
================================================================================
```

### Generate Patient Data
```bash
python src/generators/generate_patients.py
```

This will create 1,000 synthetic patient records with realistic demographics.

Expected output:
```
Generating patients: 100%|████████████| 1000/1000 [00:03<00:00, 285.71it/s]
Successfully inserted 1000 patients
```

### Generate Reference Data (Departments & Physicians)
```bash
python src/generators/generate_reference_data.py
```

This creates:
- 6 hospital departments (Emergency, ICU, Medical, Surgical, Obstetrics, Pediatrics)
- 50 physicians distributed across departments

Expected output:
```
Inserted department: Emergency Department (20 beds)
Inserted department: Intensive Care Unit (15 beds)
...
Generating physicians: 100%|████████████| 50/50 [00:01<00:00, 45.23it/s]
Successfully inserted 50 physicians
```

### Generate Encounters (Hospital Visits)
```bash
python src/generators/generate_encounters.py
```

This creates 5,000 patient encounters over the past 90 days with:
- Realistic admission patterns (more on weekdays, surge on Mondays)
- Distribution: 40% Emergency, 50% Scheduled, 10% Transfer
- Length of stay: 1-10 days
- Assigned physicians from correct departments

Expected output:
```
Retrieved 1000 patient keys
Retrieved physicians for 6 departments
Generating encounters: 100%|████████████| 5000/5000 [00:08<00:00, 625.43it/s]
Successfully inserted 5000 encounters

Summary:
- Total encounters: 5000
- Date range: 2025-12-26 to 2026-03-25 (90 days)
- Average per day: 55.6 encounters
```

### Generate Bed Events (Occupancy Tracking)
```bash
python src/generators/generate_bed_events.py
```

For each hospital encounter, this creates:
- bed_assigned event (at admission time)
- bed_discharged event (at discharge time)

This enables bed utilization analysis by tracking when beds are occupied/available.

Expected output:
```
Retrieved 5000 encounters for bed event generation
Retrieved bed capacity for 6 departments
Generating bed events: 100%|████████████| 5000/5000 [00:01<00:00, 3845.23it/s]
Inserting bed events: 100%|████████████| 10000/10000 [00:03<00:00, 2876.54it/s]
Successfully inserted 10000 bed events

Summary:
- Total encounters processed: 5000
- Total bed events created: 10000
- Events per encounter: 2 (assigned + discharged)
```

## Project Structure

```
healthcare-ops-analytics/
├── config/              # Configuration settings
├── sql/                 # Database schema and analytics queries
├── src/                 # Python source code
│   ├── generators/      # Data generation scripts
│   └── utils/           # Utility functions
├── logs/                # Application logs
├── .env                 # Environment variables (not in git)
└── requirements.txt     # Python dependencies
```

## Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)**: System architecture and design decisions
- **[CONTRIBUTING.md](CONTRIBUTING.md)**: Development setup and coding standards
- **[sql/analytics/README.md](sql/analytics/README.md)**: Analytics query documentation

## Type 2 Slowly Changing Dimensions

Track complete history of patient demographic changes:
```python
# Update patient address (preserves old address in history)
from utils.scd2_handler import update_patient_scd2

update_patient_scd2(
    patient_id="abc-123",
    changes={'address': '456 New St', 'city': 'Boston'}
)
```

Query patient data as it existed at any point in time:
```sql
-- Patient address on March 1, 2025
SELECT address FROM dim_patients
WHERE patient_id = 'abc-123'
  AND valid_from <= '2025-03-01'
  AND valid_to > '2025-03-01';
```

See [docs/SCD2_GUIDE.md](docs/SCD2_GUIDE.md) for complete guide.

---

## Analytics Queries (legacy anchor — see below)

Track historical changes to patient demographics:
```python
from src.utils.scd2_handler import update_patient_scd2

# Patient moved — creates a new versioned record, preserves the old one
result = update_patient_scd2(
    patient_id="<uuid>",
    changes={"address": "456 New Street", "city": "Boston", "state": "MA"},
)
# {'success': True, 'message': 'Created version 2', 'new_patient_key': 1042}
```

Run the SCD2 demo:
```bash
python src/demo_scd2.py
```

## Features Implemented

- [x] Dimensional data model with fact and dimension tables
- [x] Synthetic data generation with realistic distributions
- [x] Centralized configuration management
- [x] Comprehensive logging system
- [x] Master orchestration script
- [x] Advanced SQL analytics queries
- [x] Professional documentation

## Roadmap

- [ ] Data quality framework (Great Expectations)
- [ ] dbt transformation layer
- [ ] Streamlit dashboard
- [ ] Predictive analytics models
- [ ] Apache Airflow orchestration
- [ ] Automated testing suite

## License

This is a portfolio project for demonstration purposes.
