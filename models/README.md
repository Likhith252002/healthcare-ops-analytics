# dbt Transformation Layer

This directory contains dbt-style data transformations following analytics engineering best practices.

## Layer Structure

### 📥 Staging Layer (`models/staging/`)
**Purpose:** Clean and standardize raw data
- Light transformations only
- Rename columns to consistent conventions
- Type casting
- One staging model per source table

**Models:**
- `stg_patients.sql` - Current patient demographics with age groups
- `stg_encounters.sql` - Standardized encounters with derived fields (LOS, day of week)

### 🔄 Intermediate Layer (`models/intermediate/`)
**Purpose:** Business logic and entity combinations
- Join multiple staging models
- Complex calculations
- Reusable building blocks

**Models:**
- `int_patient_encounters.sql` - Enriched encounters with full patient + department + physician context

### 📊 Marts Layer (`models/marts/`)
**Purpose:** Analysis-ready datasets for specific business questions
- Aggregations
- Wide tables optimized for BI tools
- Department/team-specific views

**Models:**
- `mart_encounter_summary.sql` - Aggregated encounter metrics by day/week/month
- `mart_patient_summary.sql` - Patient lifetime statistics

## Data Flow

```
Raw Tables (PostgreSQL)
        │
        ▼
┌──────────────────────────────────┐
│         STAGING LAYER            │
│  stg_patients    stg_encounters  │
│  (clean + cast)  (clean + cast)  │
└───────────────┬──────────────────┘
                │
                ▼
┌──────────────────────────────────┐
│       INTERMEDIATE LAYER         │
│     int_patient_encounters       │
│  (join patients + encounters +   │
│   departments + physicians)      │
└───────────────┬──────────────────┘
                │
                ▼
┌──────────────────────────────────┐
│           MARTS LAYER            │
│  mart_encounter_summary          │  ← Business reporting
│  mart_patient_summary            │  ← Patient analytics
└──────────────────────────────────┘
```

## Naming Conventions

| Prefix | Layer | Description |
|--------|-------|-------------|
| `stg_` | Staging | One-to-one with source tables, cleaned |
| `int_` | Intermediate | Joins and business logic |
| `mart_` | Marts | Final aggregated models for analytics |

## Running with dbt

```bash
# Install dbt
pip install dbt-postgres

# Initialize dbt project
dbt init healthcare_analytics

# Run all models
dbt run

# Run specific layer
dbt run --select staging
dbt run --select intermediate
dbt run --select marts

# Test models
dbt test

# Generate documentation
dbt docs generate
dbt docs serve
```

## Running as Plain SQL (Without dbt)

Since these use `{{ ref() }}` and `{{ source() }}` syntax, substitute manually:

```sql
-- Replace {{ source('public', 'dim_patients') }} with dim_patients
-- Replace {{ ref('stg_patients') }} with the staging query as a CTE

-- Example: Run stg_patients manually
SELECT
    patient_key,
    patient_id,
    CONCAT(first_name, ' ', last_name) AS full_name,
    EXTRACT(YEAR FROM AGE(date_of_birth)) AS age,
    ...
FROM dim_patients
WHERE is_current = TRUE;
```
