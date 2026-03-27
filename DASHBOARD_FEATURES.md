# Dashboard Features

## Overview

Interactive Streamlit dashboard with 6 pages covering operations, analytics, and predictions.

**Access:** `streamlit run dashboard/app.py` → http://localhost:8501

---

## 🏠 Home Page

**Purpose:** High-level overview and quick navigation

**Features:**
- 4 key metrics cards (patients, encounters, departments, beds)
- 30-day daily admissions trend line chart
- Admission type distribution pie chart
- Data freshness indicator (last update timestamp)
- Quick links to all dashboard pages

**Use Case:** Executive summary for leadership and quick status checks

---

## 📊 Operations Dashboard

**Purpose:** Real-time operational metrics and KPIs

**Features:**
- Time period selector (7/14/30/60/90 days)
- 4 KPI metrics: admissions, avg LOS, emergency %, bed utilization
- Daily admission trends (total/emergency/scheduled breakdown)
- Department volume horizontal bar chart
- Length of stay distribution categories
- Hourly admission patterns line chart
- Department performance detail table (5 columns)

**Use Case:** Daily operations monitoring, capacity planning, department comparison

---

## 👥 Patient Analytics

**Purpose:** Patient demographics and behavior analysis

**Features:**
- **Demographics Tab:**
  - 4 summary metrics (total patients, avg age, gender split, top insurance)
  - Age distribution bar chart (5 age groups)
  - Gender distribution pie chart
  - Insurance type horizontal bar chart
  - Geographic distribution (top 10 states)

- **Search Tab:**
  - Name-based patient search (first or last name)
  - Search results table (up to 50 patients)
  - Individual patient detail view
  - Encounter history viewer (all visits per patient)
  - Sortable and filterable results

- **Visit Patterns Tab:**
  - Top 10 frequent patients table
  - Visit frequency distribution histogram
  - 30-day readmission tracking with dual-axis chart
  - Average readmission rate metric

**Use Case:** Patient population analysis, care coordination, readmission reduction

---

## 🏥 Department Performance

**Purpose:** Department comparison and efficiency metrics

**Features:**
- Department selector (all departments or individual)
- Time period filter (7-90 days)

- **Comparison View (All Departments):**
  - 4 summary metrics across all departments
  - Encounter volume horizontal bar chart
  - Average LOS comparison chart
  - Emergency admission % chart
  - Encounters per physician efficiency metric
  - Detailed metrics table (8 columns)

- **Individual Department View:**
  - 4 department-specific KPIs
  - Daily admission trend line chart
  - Top 10 chief complaints horizontal bar
  - Admission type breakdown pie chart

**Use Case:** Department benchmarking, resource allocation, workload balancing

---

## 📈 Advanced Analytics

**Purpose:** Statistical analysis and trend forecasting

**Features:**
- **Statistical Summary Tab:**
  - 8 LOS statistics (mean, median, Q1, Q3, IQR, stddev, min, max)
  - LOS distribution histogram (50 bins, <30 days)
  - Mean and median reference lines

- **Trends & Forecasting Tab:**
  - Weekly admission trends with dual-axis (volume + LOS)
  - Day-of-week pattern bar chart
  - Hour-of-day pattern line chart

- **Cohort Analysis Tab:**
  - Monthly cohorts with retention tracking
  - Retention % for months 1, 2, 3
  - Initial cohort size and retention percentages
  - Last 12 cohorts displayed

**Use Case:** Strategic planning, seasonality analysis, patient retention initiatives

---

## 🔮 Predictive Analytics

**Purpose:** Risk scoring and forecasting tools

**Features:**
- **Readmission Risk Calculator:**
  - 6 input factors (age, LOS, prior visits, admission type, insurance, chronic condition)
  - Rule-based scoring (0-100 scale)
  - Risk level classification (🔴 High ≥70, 🟡 Moderate 40-69, 🟢 Low <40)
  - Contributing risk factors list
  - Actionable recommendations per tier

- **LOS Prediction:**
  - Department-specific median baseline
  - Adjustment factors (admission type, age group)
  - Predicted LOS with confidence interval (±20%)
  - Historical distribution comparison
  - Department sample size display

**Use Case:** Discharge planning, resource forecasting, care management prioritization

---

## Technical Implementation

**Stack:**
- Streamlit 1.28+
- Plotly 5.17+ (interactive charts)
- Pandas 2.1+
- PostgreSQL (direct connection)

**Security:**
- SQL parameterization (no f-string interpolation)
- Proper connection closing
- Secrets management (.gitignored)

**Performance:**
- Caching with `@st.cache_data`
- Efficient SQL queries
- Materialized views support

**Deployment:**
- Local development (localhost:8501)
- Streamlit Cloud (free tier)
- Docker containerization
- Self-hosted options

---

## User Roles

**Executives/Leadership:**
- Home page for quick overview
- Operations dashboard for KPIs
- Department comparison for resource allocation

**Operations Managers:**
- Operations dashboard (detailed metrics)
- Department performance (efficiency tracking)
- Advanced analytics (trend identification)

**Care Coordinators:**
- Patient analytics (demographics, search)
- Visit patterns (readmission tracking)
- Predictions (risk scoring)

**Data Analysts:**
- Advanced analytics (statistical analysis)
- Cohort analysis (retention metrics)
- All raw data tables for export
