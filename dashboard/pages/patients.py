import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))
from utils.db_connection import get_connection


def show_patient_analytics():
    """Display patient analytics with demographics and search"""

    st.title("👥 Patient Analytics")
    st.markdown("Demographics, visit patterns, and patient search")
    st.markdown("---")

    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["📊 Demographics", "🔍 Patient Search", "📈 Visit Patterns"])

    # Tab 1: Demographics
    with tab1:
        show_demographics()

    # Tab 2: Patient Search
    with tab2:
        show_patient_search()

    # Tab 3: Visit Patterns
    with tab3:
        show_visit_patterns()


def show_demographics():
    """Display patient demographics visualizations"""

    st.subheader("📊 Patient Demographics")

    conn = get_connection()

    # Summary stats
    col1, col2, col3, col4 = st.columns(4)

    # Total patients
    df_total = pd.read_sql("SELECT COUNT(*) as count FROM dim_patients WHERE is_current = TRUE", conn)
    total_patients = df_total['count'].iloc[0]

    # Average age
    df_age = pd.read_sql("""
        SELECT AVG(EXTRACT(YEAR FROM AGE(date_of_birth))) as avg_age
        FROM dim_patients
        WHERE is_current = TRUE
    """, conn)
    avg_age = df_age['avg_age'].iloc[0] if df_age['avg_age'].iloc[0] else 0

    # Gender distribution
    df_gender = pd.read_sql("""
        SELECT gender, COUNT(*) as count
        FROM dim_patients
        WHERE is_current = TRUE
        GROUP BY gender
    """, conn)

    # Insurance distribution
    df_insurance = pd.read_sql("""
        SELECT insurance_type, COUNT(*) as count
        FROM dim_patients
        WHERE is_current = TRUE
        GROUP BY insurance_type
        ORDER BY count DESC
    """, conn)

    with col1:
        st.metric("Total Patients", f"{total_patients:,}")

    with col2:
        st.metric("Average Age", f"{avg_age:.1f} years")

    with col3:
        if not df_gender.empty:
            most_common_gender = df_gender.loc[df_gender['count'].idxmax(), 'gender']
            gender_pct = (df_gender.loc[df_gender['count'].idxmax(), 'count'] / total_patients) * 100
            st.metric("Most Common Gender", f"{most_common_gender} ({gender_pct:.1f}%)")

    with col4:
        if not df_insurance.empty:
            most_common_insurance = df_insurance.loc[0, 'insurance_type']
            st.metric("Top Insurance", most_common_insurance)

    st.markdown("---")

    # Charts
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Age Distribution")

        df_age_dist = pd.read_sql("""
            SELECT
                CASE
                    WHEN EXTRACT(YEAR FROM AGE(date_of_birth)) < 18 THEN '0-17'
                    WHEN EXTRACT(YEAR FROM AGE(date_of_birth)) BETWEEN 18 AND 34 THEN '18-34'
                    WHEN EXTRACT(YEAR FROM AGE(date_of_birth)) BETWEEN 35 AND 54 THEN '35-54'
                    WHEN EXTRACT(YEAR FROM AGE(date_of_birth)) BETWEEN 55 AND 74 THEN '55-74'
                    ELSE '75+'
                END as age_group,
                COUNT(*) as count
            FROM dim_patients
            WHERE is_current = TRUE
            GROUP BY age_group
            ORDER BY
                CASE age_group
                    WHEN '0-17' THEN 1
                    WHEN '18-34' THEN 2
                    WHEN '35-54' THEN 3
                    WHEN '55-74' THEN 4
                    ELSE 5
                END
        """, conn)

        if not df_age_dist.empty:
            fig = px.bar(
                df_age_dist,
                x='age_group',
                y='count',
                labels={'age_group': 'Age Group', 'count': 'Patients'},
                color='count',
                color_continuous_scale='Blues'
            )
            fig.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Gender Distribution")

        if not df_gender.empty:
            fig = px.pie(
                df_gender,
                values='count',
                names='gender',
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Insurance Type Distribution")

        if not df_insurance.empty:
            fig = px.bar(
                df_insurance,
                x='count',
                y='insurance_type',
                orientation='h',
                labels={'count': 'Patients', 'insurance_type': 'Insurance Type'},
                color='count',
                color_continuous_scale='Greens'
            )
            fig.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Geographic Distribution (Top 10 States)")

        df_states = pd.read_sql("""
            SELECT state, COUNT(*) as count
            FROM dim_patients
            WHERE is_current = TRUE
            GROUP BY state
            ORDER BY count DESC
            LIMIT 10
        """, conn)

        if not df_states.empty:
            fig = px.bar(
                df_states,
                x='state',
                y='count',
                labels={'state': 'State', 'count': 'Patients'},
                color='count',
                color_continuous_scale='Reds'
            )
            fig.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig, use_container_width=True)

    conn.close()


def show_patient_search():
    """Search for specific patients and view their details"""

    st.subheader("🔍 Patient Search")

    # Search input
    col1, col2 = st.columns([3, 1])

    with col1:
        search_term = st.text_input(
            "Search by name (first or last)",
            placeholder="Enter patient name..."
        )

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        search_button = st.button("Search", type="primary")

    if search_term or search_button:
        conn = get_connection()

        # Parameterized LIKE pattern — prevents SQL injection
        like_pattern = f'%{search_term}%'

        df_patients = pd.read_sql("""
            SELECT
                patient_id,
                first_name || ' ' || last_name as name,
                EXTRACT(YEAR FROM AGE(date_of_birth)) as age,
                gender,
                insurance_type,
                city || ', ' || state as location
            FROM dim_patients
            WHERE is_current = TRUE
              AND (LOWER(first_name) LIKE LOWER(%s)
                   OR LOWER(last_name) LIKE LOWER(%s))
            ORDER BY last_name, first_name
            LIMIT 50
        """, conn, params=[like_pattern, like_pattern])

        if not df_patients.empty:
            st.success(f"Found {len(df_patients)} patient(s)")

            # Display results
            st.dataframe(
                df_patients,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "patient_id": st.column_config.TextColumn("Patient ID", width="medium"),
                    "name": st.column_config.TextColumn("Name", width="medium"),
                    "age": st.column_config.NumberColumn("Age", format="%d"),
                    "gender": st.column_config.TextColumn("Gender", width="small"),
                    "insurance_type": st.column_config.TextColumn("Insurance", width="medium"),
                    "location": st.column_config.TextColumn("Location", width="medium")
                }
            )

            # Patient detail view
            st.markdown("---")
            st.subheader("Patient Details")

            selected_patient_id = st.selectbox(
                "Select a patient to view details",
                options=df_patients['patient_id'].tolist(),
                format_func=lambda x: df_patients[df_patients['patient_id'] == x]['name'].iloc[0]
            )

            if selected_patient_id:
                # Parameterized query for encounter history
                df_encounters = pd.read_sql("""
                    SELECT
                        e.admission_date,
                        e.discharge_date,
                        d.department_name,
                        e.admission_type,
                        e.chief_complaint,
                        ROUND(EXTRACT(EPOCH FROM (e.discharge_date - e.admission_date)) / 86400, 1) as los_days
                    FROM fact_encounters e
                    JOIN dim_departments d ON e.department_key = d.department_key
                    WHERE e.patient_id = %s
                    ORDER BY e.admission_date DESC
                """, conn, params=[selected_patient_id])

                if not df_encounters.empty:
                    st.info(f"Total encounters: {len(df_encounters)}")
                    st.dataframe(
                        df_encounters,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "admission_date": st.column_config.DatetimeColumn("Admitted", format="YYYY-MM-DD HH:mm"),
                            "discharge_date": st.column_config.DatetimeColumn("Discharged", format="YYYY-MM-DD HH:mm"),
                            "department_name": st.column_config.TextColumn("Department"),
                            "admission_type": st.column_config.TextColumn("Type"),
                            "chief_complaint": st.column_config.TextColumn("Chief Complaint"),
                            "los_days": st.column_config.NumberColumn("LOS (days)", format="%.1f")
                        }
                    )
                else:
                    st.warning("No encounters found for this patient")
        else:
            st.warning("No patients found matching your search")

        conn.close()
    else:
        st.info("Enter a name to search for patients")


def show_visit_patterns():
    """Display patient visit patterns and trends"""

    st.subheader("📈 Visit Patterns")

    conn = get_connection()

    # Frequent patients
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Top 10 Frequent Patients")

        df_frequent = pd.read_sql("""
            SELECT
                p.first_name || ' ' || p.last_name as patient_name,
                COUNT(e.encounter_key) as visit_count,
                ROUND(AVG(EXTRACT(EPOCH FROM (e.discharge_date - e.admission_date)) / 86400)::numeric, 1) as avg_los
            FROM dim_patients p
            JOIN fact_encounters e ON p.patient_id = e.patient_id
            WHERE p.is_current = TRUE
            GROUP BY p.patient_key, p.first_name, p.last_name
            HAVING COUNT(e.encounter_key) >= 2
            ORDER BY visit_count DESC
            LIMIT 10
        """, conn)

        if not df_frequent.empty:
            st.dataframe(
                df_frequent,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "patient_name": "Patient",
                    "visit_count": st.column_config.NumberColumn("Visits", format="%d"),
                    "avg_los": st.column_config.NumberColumn("Avg LOS", format="%.1f")
                }
            )
        else:
            st.info("No frequent patients found")

    with col2:
        st.markdown("#### Visit Frequency Distribution")

        df_visit_dist = pd.read_sql("""
            WITH visit_counts AS (
                SELECT
                    p.patient_key,
                    COUNT(e.encounter_key) as visits
                FROM dim_patients p
                LEFT JOIN fact_encounters e ON p.patient_id = e.patient_id
                WHERE p.is_current = TRUE
                GROUP BY p.patient_key
            )
            SELECT
                CASE
                    WHEN visits = 0 THEN '0 visits'
                    WHEN visits = 1 THEN '1 visit'
                    WHEN visits BETWEEN 2 AND 3 THEN '2-3 visits'
                    WHEN visits BETWEEN 4 AND 5 THEN '4-5 visits'
                    ELSE '6+ visits'
                END as visit_category,
                COUNT(*) as patient_count
            FROM visit_counts
            GROUP BY visit_category
            ORDER BY
                CASE visit_category
                    WHEN '0 visits' THEN 1
                    WHEN '1 visit' THEN 2
                    WHEN '2-3 visits' THEN 3
                    WHEN '4-5 visits' THEN 4
                    ELSE 5
                END
        """, conn)

        if not df_visit_dist.empty:
            fig = px.bar(
                df_visit_dist,
                x='visit_category',
                y='patient_count',
                labels={'visit_category': 'Visit Frequency', 'patient_count': 'Patients'},
                color='patient_count',
                color_continuous_scale='Purples'
            )
            fig.update_layout(showlegend=False, height=350)
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Readmissions analysis
    st.markdown("#### 30-Day Readmissions")

    df_readmissions = pd.read_sql("""
        WITH encounters_with_next AS (
            SELECT
                patient_id,
                admission_date,
                discharge_date,
                LEAD(admission_date) OVER (PARTITION BY patient_id ORDER BY admission_date) as next_admission
            FROM fact_encounters
        )
        SELECT
            DATE_TRUNC('month', discharge_date) as month,
            COUNT(*) as total_discharges,
            COUNT(CASE WHEN next_admission - discharge_date <= INTERVAL '30 days' THEN 1 END) as readmissions_30d,
            ROUND(COUNT(CASE WHEN next_admission - discharge_date <= INTERVAL '30 days' THEN 1 END)::numeric /
                  NULLIF(COUNT(*), 0) * 100, 1) as readmission_rate
        FROM encounters_with_next
        WHERE discharge_date IS NOT NULL
        GROUP BY DATE_TRUNC('month', discharge_date)
        ORDER BY month DESC
        LIMIT 12
    """, conn)

    if not df_readmissions.empty:
        col1, col2 = st.columns([2, 1])

        with col1:
            fig = go.Figure()

            fig.add_trace(go.Bar(
                x=df_readmissions['month'],
                y=df_readmissions['readmissions_30d'],
                name='30-Day Readmissions',
                marker_color='#ff7f0e'
            ))

            fig.add_trace(go.Scatter(
                x=df_readmissions['month'],
                y=df_readmissions['readmission_rate'],
                name='Readmission Rate (%)',
                yaxis='y2',
                line=dict(color='#d62728', width=3),
                mode='lines+markers'
            ))

            fig.update_layout(
                xaxis_title="Month",
                yaxis_title="Readmissions",
                yaxis2=dict(
                    title="Rate (%)",
                    overlaying='y',
                    side='right'
                ),
                hovermode='x unified',
                height=400
            )

            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Summary stats
            avg_rate = df_readmissions['readmission_rate'].mean()
            total_readmissions = df_readmissions['readmissions_30d'].sum()

            st.metric("Avg Readmission Rate", f"{avg_rate:.1f}%")
            st.metric("Total 30-Day Readmissions", f"{total_readmissions:,}")

            st.info("""
            **Readmission Rate:**
            - Industry benchmark: ~15%
            - Target: <10%
            """)

    conn.close()
