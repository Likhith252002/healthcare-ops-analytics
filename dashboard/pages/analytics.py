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


def show_advanced_analytics():
    """Display advanced analytics with statistical analysis"""

    st.title("📈 Advanced Analytics")
    st.markdown("Statistical analysis, trends, and cohort insights")
    st.markdown("---")

    # Tabs
    tab1, tab2, tab3 = st.tabs(["📊 Statistical Summary", "📈 Trends & Forecasting", "👥 Cohort Analysis"])

    with tab1:
        show_statistical_summary()

    with tab2:
        show_trends()

    with tab3:
        show_cohort_analysis()


def show_statistical_summary():
    """Display statistical summary metrics"""

    st.subheader("📊 Statistical Summary")

    conn = get_connection()

    # Length of stay statistics
    st.markdown("#### Length of Stay Analysis")

    df_los_stats = pd.read_sql("""
        SELECT
            AVG(EXTRACT(EPOCH FROM (discharge_date - admission_date)) / 86400) as mean_los,
            PERCENTILE_CONT(0.5) WITHIN GROUP (
                ORDER BY EXTRACT(EPOCH FROM (discharge_date - admission_date)) / 86400
            ) as median_los,
            PERCENTILE_CONT(0.25) WITHIN GROUP (
                ORDER BY EXTRACT(EPOCH FROM (discharge_date - admission_date)) / 86400
            ) as q1_los,
            PERCENTILE_CONT(0.75) WITHIN GROUP (
                ORDER BY EXTRACT(EPOCH FROM (discharge_date - admission_date)) / 86400
            ) as q3_los,
            STDDEV(EXTRACT(EPOCH FROM (discharge_date - admission_date)) / 86400) as stddev_los,
            MIN(EXTRACT(EPOCH FROM (discharge_date - admission_date)) / 86400) as min_los,
            MAX(EXTRACT(EPOCH FROM (discharge_date - admission_date)) / 86400) as max_los
        FROM fact_encounters
    """, conn)

    if not df_los_stats.empty:
        stats = df_los_stats.iloc[0]

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Mean LOS", f"{stats['mean_los']:.2f} days")
            st.metric("Median LOS", f"{stats['median_los']:.2f} days")

        with col2:
            st.metric("Q1 (25th %ile)", f"{stats['q1_los']:.2f} days")
            st.metric("Q3 (75th %ile)", f"{stats['q3_los']:.2f} days")

        with col3:
            st.metric("Std Deviation", f"{stats['stddev_los']:.2f} days")
            iqr = stats['q3_los'] - stats['q1_los']
            st.metric("IQR", f"{iqr:.2f} days")

        with col4:
            st.metric("Min LOS", f"{stats['min_los']:.2f} days")
            st.metric("Max LOS", f"{stats['max_los']:.2f} days")

    st.markdown("---")

    # LOS distribution histogram
    st.markdown("#### Length of Stay Distribution")

    df_los = pd.read_sql("""
        SELECT EXTRACT(EPOCH FROM (discharge_date - admission_date)) / 86400 as los_days
        FROM fact_encounters
        WHERE EXTRACT(EPOCH FROM (discharge_date - admission_date)) / 86400 <= 30
    """, conn)

    if not df_los.empty:
        fig = px.histogram(
            df_los,
            x='los_days',
            nbins=50,
            labels={'los_days': 'Length of Stay (days)', 'count': 'Frequency'},
            color_discrete_sequence=['#1f77b4']
        )
        fig.add_vline(
            x=df_los['los_days'].mean(),
            line_dash="dash",
            line_color="red",
            annotation_text="Mean",
            annotation_position="top"
        )
        fig.add_vline(
            x=df_los['los_days'].median(),
            line_dash="dash",
            line_color="green",
            annotation_text="Median",
            annotation_position="top"
        )
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    conn.close()


def show_trends():
    """Display trend analysis and patterns"""

    st.subheader("📈 Trends & Patterns")

    conn = get_connection()

    # Weekly trends
    st.markdown("#### Weekly Admission Trends")

    df_weekly = pd.read_sql("""
        SELECT
            DATE_TRUNC('week', admission_date) as week_start,
            COUNT(*) as admissions,
            AVG(EXTRACT(EPOCH FROM (discharge_date - admission_date)) / 86400) as avg_los
        FROM fact_encounters
        WHERE admission_date > CURRENT_DATE - INTERVAL '90 days'
        GROUP BY DATE_TRUNC('week', admission_date)
        ORDER BY week_start
    """, conn)

    if not df_weekly.empty:
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df_weekly['week_start'],
            y=df_weekly['admissions'],
            name='Weekly Admissions',
            line=dict(color='#1f77b4', width=3),
            yaxis='y'
        ))

        fig.add_trace(go.Scatter(
            x=df_weekly['week_start'],
            y=df_weekly['avg_los'],
            name='Avg LOS',
            line=dict(color='#ff7f0e', width=3),
            yaxis='y2'
        ))

        fig.update_layout(
            xaxis_title="Week",
            yaxis=dict(title="Admissions", side='left'),
            yaxis2=dict(title="Avg LOS (days)", overlaying='y', side='right'),
            hovermode='x unified',
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Day of week pattern
    st.markdown("#### Day of Week Patterns")

    col1, col2 = st.columns(2)

    with col1:
        df_dow = pd.read_sql("""
            SELECT
                CASE EXTRACT(DOW FROM admission_date)
                    WHEN 0 THEN 'Sunday'
                    WHEN 1 THEN 'Monday'
                    WHEN 2 THEN 'Tuesday'
                    WHEN 3 THEN 'Wednesday'
                    WHEN 4 THEN 'Thursday'
                    WHEN 5 THEN 'Friday'
                    WHEN 6 THEN 'Saturday'
                END as day_name,
                EXTRACT(DOW FROM admission_date) as dow,
                COUNT(*) as admissions
            FROM fact_encounters
            GROUP BY EXTRACT(DOW FROM admission_date)
            ORDER BY dow
        """, conn)

        if not df_dow.empty:
            fig = px.bar(
                df_dow,
                x='day_name',
                y='admissions',
                labels={'day_name': 'Day of Week', 'admissions': 'Admissions'},
                color='admissions',
                color_continuous_scale='Blues'
            )
            fig.update_layout(showlegend=False, height=350)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        df_hour = pd.read_sql("""
            SELECT
                EXTRACT(HOUR FROM admission_date) as hour,
                COUNT(*) as admissions
            FROM fact_encounters
            GROUP BY EXTRACT(HOUR FROM admission_date)
            ORDER BY hour
        """, conn)

        if not df_hour.empty:
            fig = px.line(
                df_hour,
                x='hour',
                y='admissions',
                markers=True,
                labels={'hour': 'Hour of Day', 'admissions': 'Admissions'}
            )
            fig.update_traces(line_color='#2ca02c', line_width=3, marker=dict(size=8))
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)

    conn.close()


def show_cohort_analysis():
    """Display cohort retention analysis"""

    st.subheader("👥 Cohort Analysis")
    st.markdown("Patient retention by first visit month")

    conn = get_connection()

    df_cohort = pd.read_sql("""
        WITH patient_first_visit AS (
            SELECT
                patient_id,
                DATE_TRUNC('month', MIN(admission_date)) as cohort_month
            FROM fact_encounters
            GROUP BY patient_id
        ),
        monthly_activity AS (
            SELECT
                pf.cohort_month,
                DATE_TRUNC('month', e.admission_date) as activity_month,
                EXTRACT(MONTH FROM AGE(
                    DATE_TRUNC('month', e.admission_date),
                    pf.cohort_month
                )) as months_since_first,
                COUNT(DISTINCT e.patient_id) as active_patients
            FROM patient_first_visit pf
            JOIN fact_encounters e ON pf.patient_id = e.patient_id
            GROUP BY pf.cohort_month, DATE_TRUNC('month', e.admission_date)
        )
        SELECT
            cohort_month,
            MAX(CASE WHEN months_since_first = 0 THEN active_patients END) as month_0,
            MAX(CASE WHEN months_since_first = 1 THEN active_patients END) as month_1,
            MAX(CASE WHEN months_since_first = 2 THEN active_patients END) as month_2,
            MAX(CASE WHEN months_since_first = 3 THEN active_patients END) as month_3
        FROM monthly_activity
        WHERE months_since_first <= 3
        GROUP BY cohort_month
        ORDER BY cohort_month DESC
        LIMIT 12
    """, conn)

    conn.close()

    if not df_cohort.empty:
        # Calculate retention rates
        df_cohort['retention_month_1'] = (
            df_cohort['month_1'] / df_cohort['month_0'] * 100
        ).fillna(0).round(1)
        df_cohort['retention_month_2'] = (
            df_cohort['month_2'] / df_cohort['month_0'] * 100
        ).fillna(0).round(1)
        df_cohort['retention_month_3'] = (
            df_cohort['month_3'] / df_cohort['month_0'] * 100
        ).fillna(0).round(1)

        st.dataframe(
            df_cohort[['cohort_month', 'month_0', 'retention_month_1', 'retention_month_2', 'retention_month_3']],
            use_container_width=True,
            hide_index=True,
            column_config={
                "cohort_month": st.column_config.DatetimeColumn("Cohort", format="YYYY-MM"),
                "month_0": st.column_config.NumberColumn("Initial Size", format="%d"),
                "retention_month_1": st.column_config.NumberColumn("Month 1 %", format="%.1f%%"),
                "retention_month_2": st.column_config.NumberColumn("Month 2 %", format="%.1f%%"),
                "retention_month_3": st.column_config.NumberColumn("Month 3 %", format="%.1f%%")
            }
        )

        st.info("""
        **Cohort retention** tracks what percentage of patients return for care after their first visit.
        Higher retention indicates better patient engagement and continuity of care.
        """)
