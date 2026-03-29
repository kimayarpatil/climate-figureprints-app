import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.figure_factory as ff
import requests
import io
import pickle
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
import warnings
warnings.filterwarnings('ignore')

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Ultimate Climate AI Dashboard",
    page_icon="🌍",
    layout="wide"
)

# ---------------- GLOBAL VARIABLES ----------------
predictions = {}  # FIX: prevent NameError

# ---------------- CUSTOM CSS ----------------
st.markdown("""
<style>
.main-header {font-size: 3.5rem; font-weight: 900; color: #1a3c5e;}
.metric-card {
    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    padding: 1.5rem;
    border-radius: 15px;
    color: white;
    text-align: center;
}
.warning-card {background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);}
.success-card {background: linear-gradient(135deg, #51cf66 0%, #40c057 100%);}
</style>
""", unsafe_allow_html=True)

# ---------------- LOAD DATA ----------------
@st.cache_data
def load_data():
    np.random.seed(42)

    years = np.arange(1880, 2031)
    months = np.tile(np.arange(1, 13), len(years))
    dates = pd.date_range('1880-01-01', periods=len(years)*12, freq='MS')

    trend = 0.0085
    warming = trend * (np.repeat(years, 12) - 1880)

    df = pd.DataFrame({
        'Date': dates,
        'Year': np.repeat(years, 12),
        'Month': months,
        'Temp': 14 + 10*np.sin(2*np.pi*months/12) + warming + np.random.normal(0, 0.8, len(dates)),
        'CO2_ppm': 280 + 2.1*(np.repeat(years, 12) - 1880)**1.2,
        'Sea_Level_mm': 1.7*(np.repeat(years, 12) - 1880),
        'Precip_mm': 800 + np.random.normal(0, 50, len(dates)),
        'Region': np.random.choice(['Global', 'Asia', 'Europe', 'Africa', 'North America'], len(dates))
    })

    df['Extreme_Event'] = np.random.choice([True, False], len(df), p=[0.02, 0.98])
    return df

df = load_data()

# ---------------- SIDEBAR ----------------
st.sidebar.header("🔍 Controls")

start_year = st.sidebar.slider("Start Year", 1880, 2025, 2000)
end_year = st.sidebar.slider("End Year", start_year, 2030, 2025)
region = st.sidebar.multiselect("Region", df['Region'].unique(), default=['Global'])

filtered_df = df[
    (df['Year'] >= start_year) &
    (df['Year'] <= end_year) &
    (df['Region'].isin(region))
].copy()

# Derived features
filtered_df['Temp_Anomaly'] = filtered_df['Temp'] - filtered_df['Temp'].mean()
filtered_df['Risk_Index'] = (
    (filtered_df['Temp'] - filtered_df['Temp'].mean()) / filtered_df['Temp'].std()
).clip(0, 100)

# ---------------- HEADER ----------------
st.markdown('<h1 class="main-header">🌍 Climate AI Dashboard</h1>', unsafe_allow_html=True)

# ---------------- METRICS ----------------
col1, col2, col3 = st.columns(3)

col1.metric("🌡️ Current Temp", f"{filtered_df['Temp'].iloc[-1]:.2f}°C")
col2.metric("🌫️ CO2", f"{filtered_df['CO2_ppm'].iloc[-1]:.0f} ppm")
col3.metric("⚠️ Events", len(filtered_df[filtered_df['Extreme_Event']]))

# ---------------- TABS ----------------
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Overview", "🤖 Prediction", "📈 Analytics", "📄 Reports"
])

# ---------------- OVERVIEW ----------------
with tab1:
    fig = px.line(filtered_df, x="Date", y="Temp", title="Temperature Trend")
    st.plotly_chart(fig, use_container_width=True)

# ---------------- PREDICTION ----------------
with tab2:
    st.header("AI Prediction")

    forecast_year = st.slider("Year", 2025, 2100, 2030)

    if st.button("Predict"):
        base = filtered_df['Temp'].iloc[-1]

        predictions = {
            "Baseline": base + 0.02*(forecast_year - 2025),
            "AI": base + np.random.normal(1.5, 0.2)
        }

        fig = px.bar(x=list(predictions.keys()), y=list(predictions.values()))
        st.plotly_chart(fig)

# ---------------- ANALYTICS ----------------
with tab3:
    corr = filtered_df[['Temp', 'CO2_ppm', 'Sea_Level_mm']].corr()
    fig = px.imshow(corr, text_auto=True)
    st.plotly_chart(fig)

# ---------------- REPORTS ----------------
with tab4:
    st.header("Generate Report")

    if st.button("Download Report"):

        pred_value = 0
        if predictions:
            pred_value = list(predictions.values())[0]

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer)

        styles = getSampleStyleSheet()

        story = [
            Paragraph("Climate Report", styles['Title']),
            Spacer(1, 20)
        ]

        table_data = [
            ["Metric", "Value"],
            ["Avg Temp", f"{filtered_df['Temp'].mean():.2f}"],
            ["CO2", f"{filtered_df['CO2_ppm'].iloc[-1]:.0f}"],
            ["Prediction", f"{pred_value:.2f}"]
        ]

        table = Table(table_data)
        table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 1, colors.black)
        ]))

        story.append(table)
        doc.build(story)

        st.download_button(
            "Download PDF",
            buffer.getvalue(),
            "report.pdf"
        )

# ---------------- FOOTER ----------------
st.markdown("---")
st.markdown("🚀 Built with Streamlit | Climate AI Project")
