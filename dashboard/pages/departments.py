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


def show_department_performance():
    """Display department performance metrics and comparisons"""

    st.title("🏥 Department Performance")
    st.markdown("Compare departments across key metrics and efficiency indicators")
    st.markdown("---")

    # Department selector
    conn = get_connection()

    df_depts = pd.read_sql("SELECT department_name FROM dim_departments ORDER BY department_name", conn)
    departments = df_depts['department_name'].tolist()

    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        selected_dept = st.selectbox("Select Department", ["All Departments"] + departments)

    with col2:
        days_back = st.selectbox("Time Period", [7, 14, 30, 60, 90], index=2)

    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        refresh = st.button("🔄 Refresh")

    conn.close()

    st.markdown("---")

    if selected_dept == "All Departments":
        show_department_comparison(days_back)
    else:
        show_single_department_detail(selected_dept, days_back)


def show_department_comparison(days_back):
    """Compare all departments across metrics"""

    st.subheader("📊 Department Comparison")

    conn = get_connection()
    start_date = datetime.now() - timedelta(days=days_back)

    # Get department metrics — parameterized start_date
    df_metrics = pd.read_sql("""
        SELECT
            d.department_name,
            d.bed_capacity,
            COUNT(e.encounter_key) as total_encounters,
            ROUND(AVG(EXTRACT(EPOCH FROM (e.discharge_date - e.admission_date)) / 86400)::numeric, 1) as avg_los,
            COUNT(CASE WHEN e.admission_type = 'Emergency' THEN 1 END) as emergency_count,
            ROUND(COUNT(CASE WHEN e.admission_type = 'Emergency' THEN 1 END)::numeric /
                  NULLIF(COUNT(e.encounter_key), 0) * 100, 1) as emergency_pct,
            (SELECT COUNT(*) FROM dim_physicians WHERE department_key = d.department_key) as physician_count
        FROM dim_departments d
        LEFT JOIN fact_encounters e ON d.department_key = e.department_key
            AND e.admission_date >= %s
        GROUP BY d.department_key, d.department_name, d.bed_capacity
        ORDER BY total_encounters DESC
    """, conn, params=[start_date])

    conn.close()

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_encounters = df_metrics['total_encounters'].sum()
        st.metric("Total Encounters", f"{total_encounters:,}")

    with col2:
        avg_los_all = df_metrics['avg_los'].mean()
        st.metric("Avg LOS (All Depts)", f"{avg_los_all:.1f} days")

    with col3:
        total_capacity = df_metrics['bed_capacity'].sum()
        st.metric("Total Bed Capacity", f"{total_capacity}")

    with col4:
        total_physicians = df_metrics['physician_count'].sum()
        st.metric("Total Physicians", f"{total_physicians}")

    st.markdown("---")

    # Comparison charts
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Encounter Volume by Department")

        fig = px.bar(
            df_metrics.sort_values('total_encounters', ascending=True),
            y='department_name',
            x='total_encounters',
            orientation='h',
            color='total_encounters',
            color_continuous_scale='Blues',
            labels={'department_name': 'Department', 'total_encounters': 'Encounters'}
        )
        fig.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### Average Length of Stay")

        fig = px.bar(
            df_metrics.sort_values('avg_los', ascending=True),
            y='department_name',
            x='avg_los',
            orientation='h',
            color='avg_los',
            color_continuous_scale='Greens',
            labels={'department_name': 'Department', 'avg_los': 'Days'}
        )
        fig.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Emergency Admission %")

        fig = px.bar(
            df_metrics.sort_values('emergency_pct', ascending=True),
            y='department_name',
            x='emergency_pct',
            orientation='h',
            color='emergency_pct',
            color_continuous_scale='Reds',
            labels={'department_name': 'Department', 'emergency_pct': 'Emergency %'}
        )
        fig.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### Encounters per Physician")

        df_metrics['encounters_per_physician'] = (
            df_metrics['total_encounters'] / df_metrics['physician_count'].replace(0, 1)
        )

        fig = px.bar(
            df_metrics.sort_values('encounters_per_physician', ascending=True),
            y='department_name',
            x='encounters_per_physician',
            orientation='h',
            color='encounters_per_physician',
            color_continuous_scale='Purples',
            labels={'department_name': 'Department', 'encounters_per_physician': 'Encounters/Physician'}
        )
        fig.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Detailed table
    st.subheader("📋 Detailed Metrics")

    st.dataframe(
        df_metrics,
        use_container_width=True,
        hide_index=True,
        column_config={
            "department_name": st.column_config.TextColumn("Department"),
            "bed_capacity": st.column_config.NumberColumn("Beds", format="%d"),
            "total_encounters": st.column_config.NumberColumn("Encounters", format="%d"),
            "avg_los": st.column_config.NumberColumn("Avg LOS", format="%.1f"),
            "emergency_count": st.column_config.NumberColumn("Emergency", format="%d"),
            "emergency_pct": st.column_config.NumberColumn("Emergency %", format="%.1f%%"),
            "physician_count": st.column_config.NumberColumn("Physicians", format="%d"),
            "encounters_per_physician": st.column_config.NumberColumn("Enc/Physician", format="%.1f")
        }
    )


def show_single_department_detail(department_name, days_back):
    """Show detailed metrics for a single department"""

    st.subheader(f"🏥 {department_name} - Detailed Analysis")

    conn = get_connection()
    start_date = datetime.now() - timedelta(days=days_back)

    # Department info and metrics — department_type removed (not in schema)
    df_info = pd.read_sql("""
        SELECT
            d.bed_capacity,
            COUNT(e.encounter_key) as total_encounters,
            ROUND(AVG(EXTRACT(EPOCH FROM (e.discharge_date - e.admission_date)) / 86400)::numeric, 1) as avg_los,
            PERCENTILE_CONT(0.5) WITHIN GROUP (
                ORDER BY EXTRACT(EPOCH FROM (e.discharge_date - e.admission_date)) / 86400
            ) as median_los,
            MIN(e.admission_date) as first_encounter,
            MAX(e.admission_date) as last_encounter,
            (SELECT COUNT(*) FROM dim_physicians WHERE department_key = d.department_key) as physician_count
        FROM dim_departments d
        LEFT JOIN fact_encounters e ON d.department_key = e.department_key
            AND e.admission_date >= %s
        WHERE d.department_name = %s
        GROUP BY d.department_key, d.bed_capacity
    """, conn, params=[start_date, department_name])

    if df_info.empty:
        st.error(f"Department '{department_name}' not found")
        conn.close()
        return

    info = df_info.iloc[0]

    # Summary cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Encounters", f"{info['total_encounters']:,}")

    with col2:
        st.metric("Avg LOS", f"{info['avg_los']:.1f} days")

    with col3:
        st.metric("Bed Capacity", f"{info['bed_capacity']}")

    with col4:
        st.metric("Physicians", f"{info['physician_count']}")

    st.markdown("---")

    # Daily trend
    st.markdown("#### 📈 Daily Admission Trend")

    df_daily = pd.read_sql("""
        SELECT
            DATE(admission_date) as date,
            COUNT(*) as admissions
        FROM fact_encounters e
        JOIN dim_departments d ON e.department_key = d.department_key
        WHERE d.department_name = %s
          AND e.admission_date >= %s
        GROUP BY DATE(admission_date)
        ORDER BY date
    """, conn, params=[department_name, start_date])

    if not df_daily.empty:
        fig = px.line(
            df_daily,
            x='date',
            y='admissions',
            markers=True,
            labels={'date': 'Date', 'admissions': 'Admissions'}
        )
        fig.update_traces(line_color='#1f77b4', line_width=3, marker=dict(size=8))
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📊 Chief Complaints (Top 10)")

        df_complaints = pd.read_sql("""
            SELECT
                chief_complaint,
                COUNT(*) as count
            FROM fact_encounters e
            JOIN dim_departments d ON e.department_key = d.department_key
            WHERE d.department_name = %s
              AND e.admission_date >= %s
            GROUP BY chief_complaint
            ORDER BY count DESC
            LIMIT 10
        """, conn, params=[department_name, start_date])

        if not df_complaints.empty:
            fig = px.bar(
                df_complaints,
                x='count',
                y='chief_complaint',
                orientation='h',
                color='count',
                color_continuous_scale='Oranges',
                labels={'chief_complaint': 'Chief Complaint', 'count': 'Count'}
            )
            fig.update_layout(
                showlegend=False, height=400,
                yaxis={'categoryorder': 'total ascending'}
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### 🕐 Admission Type Breakdown")

        df_types = pd.read_sql("""
            SELECT
                admission_type,
                COUNT(*) as count
            FROM fact_encounters e
            JOIN dim_departments d ON e.department_key = d.department_key
            WHERE d.department_name = %s
              AND e.admission_date >= %s
            GROUP BY admission_type
            ORDER BY count DESC
        """, conn, params=[department_name, start_date])

        if not df_types.empty:
            fig = px.pie(
                df_types,
                values='count',
                names='admission_type',
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

    conn.close()
