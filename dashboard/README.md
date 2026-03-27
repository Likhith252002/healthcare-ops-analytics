# Healthcare Operations Dashboard

Interactive Streamlit dashboard for exploring healthcare analytics.

## Running the Dashboard

### Local Development
```bash
# From project root
streamlit run dashboard/app.py
```

The dashboard will open in your browser at http://localhost:8501

### Features

**🏠 Home Page**
- Overview metrics (patients, encounters, departments)
- Recent admission trends (30-day chart)
- Admission type distribution
- Quick navigation

**📊 Operations Dashboard**
- Real-time KPIs (admissions, LOS, emergency %, bed utilization)
- Daily admission trends with emergency/scheduled breakdown
- Department volume comparison
- Length of stay distribution
- Hourly admission patterns
- Department performance table

**Interactive features:**
- Adjustable time period (7/14/30/60/90 days)
- Refresh button for latest data
- Hover tooltips on all charts
- Sortable department details table

**👥 Patient Analytics** (Coming soon)
- Demographics breakdown
- Visit history analysis
- Readmission tracking

**🏥 Department Performance** (Coming soon)
- Department comparison
- Resource utilization
- Efficiency metrics

**📈 Advanced Analytics** (Coming soon)
- Cohort analysis
- Trend visualization
- Statistical summaries

**🔮 Predictions** (Coming soon)
- Readmission risk scoring
- Length of stay forecasting
- ML model results

## Configuration

Dashboard connects to PostgreSQL using environment variables from `.env`:
- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`

## Deployment

### Streamlit Cloud

1. Push code to GitHub
2. Go to https://streamlit.io/cloud
3. Connect repository
4. Set secrets in dashboard settings:
```toml
[postgres]
host = "your-host"
port = "5432"
database = "healthcare_ops"
user = "your-user"
password = "your-password"
```
5. Deploy

### Docker
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "dashboard/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

Build and run:
```bash
docker build -t healthcare-dashboard .
docker run -p 8501:8501 healthcare-dashboard
```

## Customization

### Adding New Pages

1. Create function for new page content
2. Add page to sidebar selectbox
3. Add conditional in main content area

### Styling

Modify CSS in `st.markdown()` sections at top of app.py
