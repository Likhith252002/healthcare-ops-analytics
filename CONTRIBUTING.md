# Contributing to Healthcare Operations Analytics

## Development Setup

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Git

### Local Setup

1. Clone repository
```bash
git clone <your-repo-url>
cd healthcare-ops-analytics
```

2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Configure environment
```bash
cp .env.example .env
# Edit .env with your PostgreSQL credentials
```

5. Run pipeline
```bash
python src/main.py
```

## Project Structure

```
healthcare-ops-analytics/
├── config/              # Configuration files
│   └── settings.py      # Centralized settings
├── logs/                # Application logs (gitignored)
├── sql/                 # SQL scripts
│   ├── schema.sql       # Database schema
│   └── analytics/       # Analytics queries
├── src/                 # Python source code
│   ├── generators/      # Data generators
│   ├── utils/           # Helper utilities
│   ├── main.py          # Main orchestration
│   └── setup_database.py
├── .env                 # Environment variables (gitignored)
├── .gitignore
├── requirements.txt
└── README.md
```

## Coding Standards

### Python
- Follow PEP 8 style guide
- Use type hints where appropriate
- Add docstrings to all functions
- Keep functions focused (single responsibility)

### SQL
- Use uppercase for SQL keywords
- Use snake_case for table and column names
- Add comments for complex queries
- Include CTEs for readability

### Git Commits
- Use conventional commit format: `feat:`, `fix:`, `docs:`, `refactor:`
- Write descriptive commit messages
- Keep commits focused (one logical change per commit)

## Testing

### Manual Testing
```bash
# Run complete pipeline
python src/main.py

# Test individual generators
python src/generators/generate_patients.py

# Test SQL queries
psql -d healthcare_ops -f sql/analytics/er_wait_times.sql
```

### Future: Automated Testing
- Unit tests for data generators
- Integration tests for pipeline
- SQL query validation

## Adding New Features

### Adding a New Data Generator
1. Create file in `src/generators/`
2. Follow existing generator pattern
3. Add configuration to `config/settings.py`
4. Update `src/main.py` to include new step
5. Update README.md documentation

### Adding a New Analytics Query
1. Create `.sql` file in `sql/analytics/`
2. Use CTEs and window functions
3. Add documentation to `sql/analytics/README.md`
4. Test query on generated data
