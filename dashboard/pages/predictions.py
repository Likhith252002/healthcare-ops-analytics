import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

import streamlit as st
import pandas as pd
import plotly.express as px

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))
from utils.db_connection import get_connection


def show_predictions():
    """Display predictive analytics tools"""

    st.title("🔮 Predictive Analytics")
    st.markdown("Risk scoring and forecasting tools")
    st.markdown("---")

    tab1, tab2 = st.tabs(["🎯 Readmission Risk", "📊 LOS Prediction"])

    with tab1:
        show_readmission_risk()

    with tab2:
        show_los_prediction()


def show_readmission_risk():
    """Display readmission risk calculator"""

    st.subheader("🎯 30-Day Readmission Risk Calculator")
    st.markdown("Estimate likelihood of patient readmission within 30 days")

    # Input form
    st.markdown("#### Patient Factors")

    col1, col2 = st.columns(2)

    with col1:
        age = st.slider("Age", 0, 100, 65)
        los = st.slider("Length of Stay (days)", 0, 30, 3)
        prior_visits = st.number_input("Prior Visits (last year)", 0, 50, 2)

    with col2:
        admission_type = st.selectbox("Admission Type", ["Emergency", "Scheduled", "Transfer"])
        insurance = st.selectbox(
            "Insurance Type",
            ["Private Insurance", "Medicare", "Medicaid", "Self-Pay/Uninsured"]
        )
        has_chronic = st.checkbox("Chronic Condition")

    # Calculate risk score (simple rule-based model)
    if st.button("Calculate Risk", type="primary"):

        # Base risk score
        risk_score = 0

        # Age factor (higher age = higher risk)
        if age > 75:
            risk_score += 25
        elif age > 65:
            risk_score += 15
        elif age > 50:
            risk_score += 5

        # LOS factor (very short or very long = higher risk)
        if los < 1:
            risk_score += 10
        elif los > 10:
            risk_score += 20

        # Prior visits (frequent visitors = higher risk)
        if prior_visits >= 5:
            risk_score += 30
        elif prior_visits >= 3:
            risk_score += 20
        elif prior_visits >= 1:
            risk_score += 10

        # Admission type
        if admission_type == "Emergency":
            risk_score += 15
        elif admission_type == "Transfer":
            risk_score += 10

        # Insurance (self-pay = higher risk)
        if insurance == "Self-Pay/Uninsured":
            risk_score += 10
        elif insurance == "Medicaid":
            risk_score += 5

        # Chronic condition
        if has_chronic:
            risk_score += 15

        # Cap at 100
        risk_score = min(risk_score, 100)

        # Display result
        st.markdown("---")
        st.markdown("### Risk Assessment Result")

        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            # Color-coded risk level
            if risk_score >= 70:
                risk_level = "HIGH RISK"
                color = "🔴"
                recommendation = "Close monitoring recommended. Consider discharge planning and follow-up within 48 hours."
            elif risk_score >= 40:
                risk_level = "MODERATE RISK"
                color = "🟡"
                recommendation = "Standard follow-up within 7 days. Ensure patient has clear discharge instructions."
            else:
                risk_level = "LOW RISK"
                color = "🟢"
                recommendation = "Standard care. Routine follow-up as scheduled."

            st.metric("Readmission Risk Score", f"{risk_score}/100")
            st.markdown(f"### {color} {risk_level}")
            st.info(recommendation)

        # Show contributing factors
        st.markdown("---")
        st.markdown("#### Risk Factors")

        factors = []
        if age > 65:
            factors.append(f"• Age {age} (senior population)")
        if los > 10:
            factors.append(f"• Extended LOS ({los} days)")
        if prior_visits >= 3:
            factors.append(f"• Frequent visitor ({prior_visits} prior visits)")
        if admission_type == "Emergency":
            factors.append("• Emergency admission")
        if insurance == "Self-Pay/Uninsured":
            factors.append("• Self-pay insurance status")
        if has_chronic:
            factors.append("• Chronic condition present")

        if factors:
            for factor in factors:
                st.markdown(factor)
        else:
            st.success("No major risk factors identified")


def show_los_prediction():
    """Display LOS prediction tool"""

    st.subheader("📊 Length of Stay Prediction")
    st.markdown("Estimate expected length of stay based on historical patterns")

    conn = get_connection()

    # Get department averages
    df_dept_avg = pd.read_sql("""
        SELECT
            d.department_name,
            AVG(EXTRACT(EPOCH FROM (e.discharge_date - e.admission_date)) / 86400) as avg_los,
            PERCENTILE_CONT(0.5) WITHIN GROUP (
                ORDER BY EXTRACT(EPOCH FROM (e.discharge_date - e.admission_date)) / 86400
            ) as median_los,
            COUNT(*) as sample_size
        FROM dim_departments d
        LEFT JOIN fact_encounters e ON d.department_key = e.department_key
        GROUP BY d.department_name
        HAVING COUNT(*) > 0
        ORDER BY d.department_name
    """, conn)

    conn.close()

    if not df_dept_avg.empty:
        # Input form
        col1, col2 = st.columns(2)

        with col1:
            selected_dept = st.selectbox("Department", df_dept_avg['department_name'].tolist())
            admission_type = st.selectbox(
                "Admission Type",
                ["Emergency", "Scheduled", "Transfer"],
                key="los_admission"
            )

        with col2:
            age_group = st.selectbox("Age Group", ["0-17", "18-34", "35-54", "55-74", "75+"])
            chief_complaint = st.text_input("Chief Complaint (optional)", "")

        if st.button("Predict LOS", type="primary"):
            # Get department baseline
            dept_data = df_dept_avg[df_dept_avg['department_name'] == selected_dept].iloc[0]
            base_los = dept_data['median_los']

            # Adjust based on factors
            predicted_los = base_los

            # Admission type adjustment
            if admission_type == "Emergency":
                predicted_los *= 1.2   # 20% longer
            elif admission_type == "Scheduled":
                predicted_los *= 0.9   # 10% shorter

            # Age adjustment
            if age_group in ["55-74", "75+"]:
                predicted_los *= 1.15  # 15% longer for seniors
            elif age_group == "0-17":
                predicted_los *= 0.85  # 15% shorter for pediatric

            # Display prediction
            st.markdown("---")
            st.markdown("### Predicted Length of Stay")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Department Median", f"{base_los:.1f} days")

            with col2:
                st.metric("Predicted LOS", f"{predicted_los:.1f} days")

            with col3:
                diff = predicted_los - base_los
                st.metric("vs Median", f"{diff:+.1f} days")

            # Confidence interval (simple ±20%)
            lower_bound = predicted_los * 0.8
            upper_bound = predicted_los * 1.2

            st.info(f"""
            **Prediction Range:** {lower_bound:.1f} - {upper_bound:.1f} days (80% confidence interval)

            **Sample Size:** {dept_data['sample_size']:.0f} historical encounters in {selected_dept}
            """)

            # Show distribution for department — parameterized query
            st.markdown("---")
            st.markdown(f"#### Historical LOS Distribution - {selected_dept}")

            conn = get_connection()
            df_dept_los = pd.read_sql("""
                SELECT EXTRACT(EPOCH FROM (discharge_date - admission_date)) / 86400 as los_days
                FROM fact_encounters e
                JOIN dim_departments d ON e.department_key = d.department_key
                WHERE d.department_name = %s
                  AND EXTRACT(EPOCH FROM (discharge_date - admission_date)) / 86400 <= 30
            """, conn, params=[selected_dept])
            conn.close()

            if not df_dept_los.empty:
                fig = px.histogram(
                    df_dept_los,
                    x='los_days',
                    nbins=30,
                    labels={'los_days': 'Length of Stay (days)'},
                    color_discrete_sequence=['#2ca02c']
                )
                fig.add_vline(
                    x=predicted_los,
                    line_dash="dash",
                    line_color="red",
                    annotation_text="Predicted",
                    annotation_position="top"
                )
                fig.update_layout(height=300, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
