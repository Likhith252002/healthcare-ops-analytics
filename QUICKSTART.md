# Quick Start Guide

## Prerequisites
- Python 3.11+
- PostgreSQL 15+

## Setup (5 minutes)
```bash
# 1. Clone repository
git clone <your-repo-url>
cd healthcare-ops-analytics

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure database
cp .env.example .env
# Edit .env with your PostgreSQL credentials

# 5. Create database
createdb healthcare_ops

# 6. Run complete pipeline
python src/main.py
```

## Expected Output
- 1,000 patients
- 6 departments
- 50 physicians
- 5,000 encounters
- 10,000 bed events

Total time: ~45 seconds

## Next Steps
- Run analytics queries: `psql -d healthcare_ops -f sql/analytics/er_wait_times.sql`
- Explore data model: See `ARCHITECTURE.md`
- Read documentation: See `README.md`
