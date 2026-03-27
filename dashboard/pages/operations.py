import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))
from utils.db_connection import get_connection


def show_operations_dashboard():
    """Display operations dashboard with KPIs and charts"""

    st.title("📊 Operations Dashboard")
    st.markdown("Real-time hospital operations metrics and performance indicators")
    st.markdown("---")

    # Date range selector
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        days_back = st.selectbox("Time Period", [7, 14, 30, 60, 90], index=2)

    with col2:
        refresh = st.button("🔄 Refresh Data")

    st.markdown("---")

    # Fetch data
    conn = get_connection()

    # KPI Metrics
    st.subheader("📈 Key Performance Indicators")

    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)

    # Admissions in period
    df_admissions = pd.read_sql("""
        SELECT COUNT(*) as count
        FROM fact_encounters
        WHERE admission_date >= %s
    """, conn, params=[start_date])
    total_admissions = df_admissions['count'].iloc[0]

    # Average LOS
    df_los = pd.read_sql("""
        SELECT AVG(EXTRACT(EPOCH FROM (discharge_date - admission_date)) / 86400) as avg_los
        FROM fact_encounters
        WHERE admission_date >= %s
    """, conn, params=[start_date])
    avg_los = df_los['avg_los'].iloc[0] if df_los['avg_los'].iloc[0] else 0

    # Emergency percentage
    df_emergency = pd.read_sql("""
        SELECT
            COUNT(CASE WHEN admission_type = 'Emergency' THEN 1 END)::float /
            NULLIF(COUNT(*), 0) * 100 as pct
        FROM fact_encounters
        WHERE admission_date >= %s
    """, conn, params=[start_date])
    emergency_pct = df_emergency['pct'].iloc[0] if df_emergency['pct'].iloc[0] else 0

    # Bed utilization
    df_beds = pd.read_sql("""
        SELECT
            COUNT(DISTINCT CASE WHEN event_type = 'bed_assigned' THEN bed_number END) as assigned,
            (SELECT SUM(bed_capacity) FROM dim_departments) as total
        FROM fact_bed_events
    """, conn)

    if df_beds['total'].iloc[0] and df_beds['total'].iloc[0] > 0:
        bed_util_pct = (df_beds['assigned'].iloc[0] / df_beds['total'].iloc[0]) * 100
    else:
        bed_util_pct = 0

    # Display KPIs
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Total Admissions",
            value=f"{total_admissions:,}",
            delta=f"Last {days_back} days"
        )

    with col2:
        st.metric(
            label="Avg Length of Stay",
            value=f"{avg_los:.1f} days",
            delta="All departments"
        )

    with col3:
        st.metric(
            label="Emergency %",
            value=f"{emergency_pct:.1f}%",
            delta="Of total admissions"
        )

    with col4:
        st.metric(
            label="Bed Utilization",
            value=f"{bed_util_pct:.1f}%",
            delta="Current capacity"
        )

    st.markdown("---")

    # Charts row 1
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📅 Daily Admission Trends")

        df_daily = pd.read_sql("""
            SELECT
                DATE(admission_date) as date,
                COUNT(*) as admissions,
                COUNT(CASE WHEN admission_type = 'Emergency' THEN 1 END) as emergency,
                COUNT(CASE WHEN admission_type = 'Scheduled' THEN 1 END) as scheduled
            FROM fact_encounters
            WHERE admission_date >= %s
            GROUP BY DATE(admission_date)
            ORDER BY date
        """, conn, params=[start_date])

        if not df_daily.empty:
            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=df_daily['date'],
                y=df_daily['admissions'],
                name='Total',
                line=dict(color='#1f77b4', width=3),
                fill='tozeroy'
            ))

            fig.add_trace(go.Scatter(
                x=df_daily['date'],
                y=df_daily['emergency'],
                name='Emergency',
                line=dict(color='#ff7f0e', width=2)
            ))

            fig.add_trace(go.Scatter(
                x=df_daily['date'],
                y=df_daily['scheduled'],
                name='Scheduled',
                line=dict(color='#2ca02c', width=2)
            ))

            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Admissions",
                hovermode='x unified',
                height=400
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available for selected period")

    with col2:
        st.subheader("🏥 Department Volume")

        df_dept = pd.read_sql("""
            SELECT
                d.department_name,
                COUNT(e.encounter_key) as encounters
            FROM dim_departments d
            LEFT JOIN fact_encounters e
                ON d.department_key = e.department_key
                AND e.admission_date >= %s
            GROUP BY d.department_name
            ORDER BY encounters DESC
        """, conn, params=[start_date])

        if not df_dept.empty:
            fig = px.bar(
                df_dept,
                x='encounters',
                y='department_name',
                orientation='h',
                title='',
                labels={'encounters': 'Encounters', 'department_name': 'Department'},
                color='encounters',
                color_continuous_scale='Blues'
            )

            fig.update_layout(
                showlegend=False,
                height=400,
                yaxis={'categoryorder': 'total ascending'}
            )

            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Charts row 2
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Length of Stay Distribution")

        df_los_dist = pd.read_sql("""
            SELECT
                CASE
                    WHEN EXTRACT(EPOCH FROM (discharge_date - admission_date)) / 86400 < 1 THEN '0-1 day'
                    WHEN EXTRACT(EPOCH FROM (discharge_date - admission_date)) / 86400 < 3 THEN '1-3 days'
                    WHEN EXTRACT(EPOCH FROM (discharge_date - admission_date)) / 86400 < 7 THEN '3-7 days'
                    ELSE '7+ days'
                END as los_category,
                COUNT(*) as count
            FROM fact_encounters
            WHERE admission_date >= %s
            GROUP BY los_category
            ORDER BY
                CASE los_category
                    WHEN '0-1 day' THEN 1
                    WHEN '1-3 days' THEN 2
                    WHEN '3-7 days' THEN 3
                    ELSE 4
                END
        """, conn, params=[start_date])

        if not df_los_dist.empty:
            fig = px.bar(
                df_los_dist,
                x='los_category',
                y='count',
                labels={'los_category': 'Length of Stay', 'count': 'Encounters'},
                color='count',
                color_continuous_scale='Viridis'
            )

            fig.update_layout(
                showlegend=False,
                height=400
            )

            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("🕐 Admission by Hour")

        df_hourly = pd.read_sql("""
            SELECT
                EXTRACT(HOUR FROM admission_date) as hour,
                COUNT(*) as admissions
            FROM fact_encounters
            WHERE admission_date >= %s
            GROUP BY EXTRACT(HOUR FROM admission_date)
            ORDER BY hour
        """, conn, params=[start_date])

        if not df_hourly.empty:
            fig = px.line(
                df_hourly,
                x='hour',
                y='admissions',
                labels={'hour': 'Hour of Day', 'admissions': 'Admissions'},
                markers=True
            )

            fig.update_traces(
                line_color='#d62728',
                line_width=3,
                marker=dict(size=8)
            )

            fig.update_layout(height=400)

            st.plotly_chart(fig, use_container_width=True)

    conn.close()

    st.markdown("---")

    # Department details table
    st.subheader("🏥 Department Performance Details")

    conn = get_connection()
    df_dept_details = pd.read_sql("""
        SELECT
            d.department_name as "Department",
            COUNT(e.encounter_key) as "Encounters",
            ROUND(AVG(EXTRACT(EPOCH FROM (e.discharge_date - e.admission_date)) / 86400)::numeric, 1) as "Avg LOS (days)",
            COUNT(CASE WHEN e.admission_type = 'Emergency' THEN 1 END) as "Emergency",
            ROUND(COUNT(CASE WHEN e.admission_type = 'Emergency' THEN 1 END)::numeric /
                  NULLIF(COUNT(e.encounter_key), 0) * 100, 1) as "Emergency %"
        FROM dim_departments d
        LEFT JOIN fact_encounters e
            ON d.department_key = e.department_key
            AND e.admission_date >= %s
        GROUP BY d.department_name
        ORDER BY "Encounters" DESC
    """, conn, params=[start_date])
    conn.close()

    st.dataframe(df_dept_details, use_container_width=True, hide_index=True)
