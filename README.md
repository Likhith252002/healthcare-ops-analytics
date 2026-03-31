# Healthcare Operations Analytics Platform

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![PostgreSQL](https://img.shields.io/badge/postgresql-15-blue.svg)](https://www.postgresql.org/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.28+-red.svg)](https://streamlit.io/)
[![dbt](https://img.shields.io/badge/dbt-1.6+-orange.svg)](https://www.getdbt.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **End-to-end healthcare analytics platform** demonstrating data engineering, analytics engineering, and business intelligence best practices.

**📊 [Live Dashboard Demo](#)** | **📚 [Documentation](docs/)** | **🎯 [Features](DASHBOARD_FEATURES.md)**

---

## 🎯 Project Overview

Professional-grade data platform showcasing:
- **Data Engineering:** ETL pipeline, dimensional modeling, Type 2 SCD
- **Analytics Engineering:** dbt transformations, data quality testing
- **Business Intelligence:** Interactive Streamlit dashboard with 6 pages
- **Production Engineering:** Error handling, testing, CI/CD

**Built for:** Portfolio, job applications, and demonstrating full-stack data skills

---

## ✨ Key Features

### 📊 Interactive Dashboard (6 Pages)
- 🏠 **Home:** Overview metrics and trends
- 📈 **Operations:** Real-time KPIs and department performance
- 👥 **Patients:** Demographics, search, visit patterns
- 🏥 **Departments:** Comparison and individual deep-dives
- 📊 **Analytics:** Statistical analysis and cohort retention
- 🔮 **Predictions:** Readmission risk and LOS forecasting

### 🏗️ Data Warehouse
- **Star schema** (Kimball methodology)
- **Type 2 SCD** for patient history tracking
- **15,000+ encounters** across 10 departments
- **5,000 synthetic patients** with realistic demographics

### 🔧 Production Features
- ✅ Incremental data loading (60x faster than full reload)
- ✅ Automated data quality checks (12 tests)
- ✅ Error handling with retry logic
- ✅ Unit tests with 80%+ coverage
- ✅ CI/CD pipeline (GitHub Actions)

### 📈 Advanced Analytics
- Window functions (running totals, rankings, moving averages)
- Recursive CTEs for hierarchical queries
- Cohort analysis and retention metrics
- Statistical summaries (percentiles, IQR, stddev)

---

## 🚀 Quick Start

### Prerequisites
```bash
# Required
Python 3.11+
PostgreSQL 15+

# Optional
Docker (for containerized deployment)
```

### Installation

1. **Clone repository**
```bash
git clone https://github.com/Likhith252002/healthcare-ops-analytics.git
cd healthcare-ops-analytics
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure database**
```bash
cp .env.example .env
# Edit .env with your PostgreSQL credentials
```

5. **Setup database and generate data**
```bash
# Create schema
python src/setup_database.py

# Generate synthetic data
python src/main.py
```

6. **Run dbt transformations** (optional)
```bash
cd dbt
dbt deps
dbt run
dbt test
```

7. **Launch dashboard**
```bash
streamlit run dashboard/app.py
```

Dashboard opens at: **http://localhost:8501** 🎉

---

## 📁 Project Structure

```
healthcare-ops-analytics/
├── src/                      # Data generation and utilities
│   ├── generators/           # Synthetic data generators
│   ├── utils/                # Database, validation, retry utilities
│   ├── setup_database.py     # Schema creation
│   └── main.py               # Data generation orchestrator
├── sql/                      # SQL queries and analytics
│   ├── schema/               # DDL statements
│   ├── analytics/            # Advanced analytics queries
│   └── viz/                  # Materialized views for BI
├── dbt/                      # dbt project
│   ├── models/               # Transformations (staging/intermediate/marts)
│   └── tests/                # Data quality tests
├── dashboard/                # Streamlit application
│   ├── pages/                # 6 dashboard pages
│   ├── app.py                # Main entry point
│   └── DEPLOYMENT.md         # Deployment guide
├── tests/                    # Unit tests
│   ├── test_validation.py
│   ├── test_retry.py
│   └── test_incremental.py
├── .github/workflows/        # CI/CD
│   └── ci.yml                # GitHub Actions pipeline
├── docs/                     # Documentation
│   ├── ARCHITECTURE.md
│   ├── SCD2_GUIDE.md
│   ├── PERFORMANCE.md
│   └── PROJECT_SUMMARY.md
└── README.md                 # This file
```

---

## 🎓 Skills Demonstrated

### Data Engineering
- ETL pipeline development
- Dimensional modeling (star schema, Kimball)
- Type 2 Slowly Changing Dimensions
- Incremental data loading patterns
- Data quality framework

### Analytics Engineering
- dbt project structure and best practices
- Staging → Intermediate → Marts layers
- Materialized views for performance
- Automated data testing

### SQL Expertise
- Complex joins and aggregations
- Window functions (ROW_NUMBER, LAG, LEAD, RANK, DENSE_RANK)
- Recursive CTEs
- PIVOT operations
- Statistical functions (PERCENTILE_CONT, STDDEV)

### Python Development
- Object-oriented design
- Error handling and retry logic
- Database connection management
- Unit testing with mocks
- Type hints and documentation

### Business Intelligence
- Interactive dashboard development (Streamlit)
- Data visualization (Plotly)
- User experience design
- Deployment strategies

### Software Engineering
- Git workflow with conventional commits
- CI/CD pipeline setup
- Documentation practices
- Security (SQL injection prevention)
- Performance optimization

---

## 📊 Project Statistics

| Metric | Value |
|--------|-------|
| **Lines of Code** | ~6,000 |
| **Files** | 70+ |
| **Git Commits** | 28+ |
| **Unit Tests** | 24 |
| **Documentation Pages** | 15+ |
| **SQL Queries** | 25+ |
| **Dashboard Pages** | 6 |
| **Charts & Visualizations** | 30+ |
| **Patients Generated** | 5,000 |
| **Encounters Generated** | 15,000+ |

---

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html

# Run specific test file
python -m pytest tests/test_validation.py -v
```

**Test Coverage:**
- ✅ Validation utilities (11 tests)
- ✅ Retry mechanisms (8 tests)
- ✅ Incremental loading (5 tests)
- ✅ Data quality checks (automated)

---

## ⚙️ Orchestration

Apache Airflow manages automated workflows:
```bash
# Start Airflow
export AIRFLOW_HOME=$(pwd)/airflow
airflow db init
airflow webserver --port 8080 &
airflow scheduler &
```

**DAGs:**
- **Daily ETL Pipeline:** Automated data generation and transformation (2 AM)
- **Data Quality Monitoring:** Hourly freshness and anomaly checks

**Access:** http://localhost:8080

See [airflow/README.md](airflow/README.md) for setup instructions.

---

## 📈 Data Quality

```bash
# Run data quality checks
python src/run_data_quality.py

# Refresh materialized views
python src/refresh_viz_metrics.py
```

**12 Automated Tests:**
- Primary key uniqueness
- Foreign key integrity
- Date logic validation
- Numerical range checks
- Required field validation
- SCD2 constraint verification

---

## 📚 Documentation

- **[DASHBOARD_FEATURES.md](DASHBOARD_FEATURES.md)** - Detailed dashboard documentation
- **[docs/PROJECT_SUMMARY.md](docs/PROJECT_SUMMARY.md)** - Architecture and overview
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System design decisions
- **[docs/SCD2_GUIDE.md](docs/SCD2_GUIDE.md)** - Type 2 SCD implementation
- **[docs/PERFORMANCE.md](docs/PERFORMANCE.md)** - Optimization strategies
- **[dashboard/DEPLOYMENT.md](dashboard/DEPLOYMENT.md)** - Deployment guide
- **[tests/README.md](tests/README.md)** - Testing guide

---

## 🚀 Deployment

### Local Development
```bash
streamlit run dashboard/app.py
```

### Streamlit Cloud (Free)
1. Push to GitHub
2. Connect at [streamlit.io/cloud](https://streamlit.io/cloud)
3. Configure secrets in dashboard settings
4. Deploy

### Docker
```bash
docker build -t healthcare-dashboard .
docker run -p 8501:8501 healthcare-dashboard
```

See [dashboard/DEPLOYMENT.md](dashboard/DEPLOYMENT.md) for detailed instructions.

---

## 🛠️ Tech Stack

**Core:**
- Python 3.11
- PostgreSQL 15
- dbt 1.6+
- Streamlit 1.28+

**Libraries:**
- pandas - Data manipulation
- plotly - Interactive visualizations
- psycopg2 - PostgreSQL adapter
- pytest - Testing framework

**DevOps:**
- GitHub Actions - CI/CD
- Docker - Containerization
- Black - Code formatting
- Flake8 - Linting

---

## 🎯 Use Cases

**Job Interviews:**
- Demonstrate end-to-end data platform knowledge
- Explain architecture and design decisions
- Walk through Type 2 SCD implementation
- Show production engineering practices

**Portfolio:**
- Professional GitHub repository
- Live dashboard demo
- Comprehensive documentation
- Clean, well-tested code

**Learning:**
- Reference for dimensional modeling
- dbt transformation patterns
- SQL analytics examples
- Dashboard design patterns

---

## 🔄 Development Workflow

```bash
# 1. Make changes to code
# 2. Run tests
pytest tests/ -v

# 3. Format code
black src/ dashboard/ tests/

# 4. Commit with conventional commit
git commit -m "feat: add new feature"

# 5. Push (CI/CD runs automatically)
git push origin main
```

---

## 🤝 Contributing

This is a portfolio project, but suggestions and improvements are welcome!

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'feat: add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📝 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**Likhith Thondamanati**
- GitHub: [@Likhith252002](https://github.com/Likhith252002)

---

## 🙏 Acknowledgments

- Inspired by real-world healthcare analytics systems
- Built using industry best practices
- Designed for portfolio and learning purposes

---

## 📊 Interactive Dashboard Preview

**Home Page:**
![Dashboard Home](docs/images/dashboard-home.png)

**Operations Dashboard:**
![Operations](docs/images/operations.png)

**Patient Analytics:**
![Patients](docs/images/patients.png)

*(Screenshots to be added after deployment)*

---

**⭐ If you found this project helpful, please star the repository!**
