# Healthcare Operations Analytics - Architecture

## System Overview

This platform simulates a 200-bed hospital's operational data and provides analytics
capabilities for demonstrating data engineering and analytics skills.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                   DATA GENERATION LAYER                      │
│  Python Scripts: Faker-based synthetic data generators      │
│  - Patients (demographics)                                   │
│  - Departments & Physicians (reference data)                 │
│  - Encounters (hospital visits)                              │
│  - Bed Events (occupancy tracking)                           │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                   DATA STORAGE LAYER                         │
│  PostgreSQL Database (Dimensional Model)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Fact Tables  │  │ Dim Tables   │  │ Staging      │      │
│  │ - encounters │  │ - patients   │  │ (future)     │      │
│  │ - bed_events │  │ - departments│  │              │      │
│  │              │  │ - physicians │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                   ANALYTICS LAYER                            │
│  SQL Queries: Pre-built operational metrics                 │
│  - ER wait times (with percentiles)                          │
│  - Bed utilization (time-series)                             │
│  - Length of stay (by department/type)                       │
│  - Daily volume trends                                       │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│              PRESENTATION LAYER (Coming Soon)                │
│  - Streamlit Dashboard                                       │
│  - Real-time Simulation                                      │
│  - Predictive Analytics                                      │
└─────────────────────────────────────────────────────────────┘
```

## Data Model

### Dimensional Model Design

**Fact Tables:**
- `fact_encounters`: One row per hospital visit (grain: encounter)
- `fact_bed_events`: One row per bed status change (grain: event)

**Dimension Tables:**
- `dim_patients`: Patient demographics (SCD Type 1, future: Type 2)
- `dim_departments`: Hospital departments with bed capacity
- `dim_physicians`: Physicians with specialty assignments

### Key Relationships
- Encounters → Patients (many-to-one)
- Encounters → Departments (many-to-one)
- Encounters → Physicians (many-to-one)
- Bed Events → Encounters (many-to-one)

## Technology Stack

### Core Technologies
- **Database**: PostgreSQL 15+
- **Language**: Python 3.11+
- **Data Generation**: Faker library
- **Orchestration**: Python subprocess (future: Apache Airflow)

### Dependencies
- `psycopg2-binary`: PostgreSQL adapter
- `pandas`: Data manipulation
- `faker`: Synthetic data generation
- `python-dotenv`: Environment configuration
- `tqdm`: Progress bars
- `numpy`: Numerical operations

## Configuration

All configurable parameters are centralized in `config/settings.py`:

**Data Volumes:**
- Patients: 1,000 records
- Physicians: 50 records
- Encounters: 5,000 records (90-day simulation)
- Bed Events: 10,000 records (2 per encounter)

**Distributions:**
- Gender: 49% M, 49% F, 2% Other
- Insurance: 45% Private, 30% Medicare, 20% Medicaid, 5% Uninsured
- Admission Type: 40% Emergency, 50% Scheduled, 10% Transfer
- Weekday Multipliers: Monday 1.2x, Weekend 0.7x baseline

## Design Decisions

### Why Dimensional Modeling?
- Optimized for analytics queries (denormalized for performance)
- Clear business logic (facts = events, dimensions = context)
- Scalable for OLAP workloads
- Industry standard for data warehouses

### Why Synthetic Data?
- HIPAA compliance (no real patient data)
- Reproducible for portfolio demonstrations
- Controllable distributions for testing edge cases
- Realistic patterns without privacy concerns

### Why PostgreSQL?
- Open-source and widely adopted
- Strong SQL analytics support (window functions, CTEs)
- Good performance for datasets up to millions of rows
- Easy local setup for development

## Performance Considerations

**Current Scale:**
- Total records: ~16,000
- Query performance: <1 second for all analytics queries
- Data generation: ~45 seconds for complete pipeline

**Batch Optimization:**
- Patient inserts: Commit every 100 records
- Encounter inserts: Commit every 100 records
- Bed event inserts: Commit every 500 records (higher batch size)

**Indexing Strategy:**
- Primary keys: Auto-indexed (SERIAL)
- Foreign keys: Explicit indexes on all FK columns
- Date columns: Indexed on admission_date, event_timestamp
- No indexes on low-cardinality columns (admission_type, gender)

## Future Enhancements

**Phase 2: Data Quality & Observability**
- Great Expectations integration
- Data quality tests (schema, business rules, statistics)
- Pipeline monitoring and alerting

**Phase 3: Transformation Layer**
- dbt implementation
- Incremental models
- Data lineage tracking
- Documentation generation

**Phase 4: Visualization**
- Streamlit dashboard
- Real-time simulation
- Interactive scenario planning

**Phase 5: Advanced Analytics**
- Demand forecasting (time-series ML)
- Anomaly detection
- Predictive models for readmissions
