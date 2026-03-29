import streamlit as st
import pandas as pd
import numpy as np
import pickle
import plotly.express as px
import os
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Climate AI Dashboard", layout="wide")

st.title("🌍 Climate AI Dashboard")

# ---------------- LOAD MODEL ----------------
if not os.path.exists("climate_model1.pkl"):
    st.error("❌ Model file missing")
    st.stop()

model = pickle.load(open("climate_model1.pkl", "rb"))
features = pickle.load(open("features.pkl", "rb"))

# ---------------- LOAD DATA ----------------
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("your_dataset.csv")  # 🔥 CHANGE THIS
        return df
    except:
        return None

df = load_data()

# ---------------- SIDEBAR INPUT ----------------
st.sidebar.header("⚙️ Input + Filters")

# Prediction inputs
year = st.sidebar.number_input("Year", 2000, 2100, 2025)
month = st.sidebar.slider("Month", 1, 12, 6)
day = 15

temp_range = st.sidebar.number_input("Temp Range", 0.0, 50.0, 10.0)
rolling_7 = st.sidebar.number_input("Rolling 7", 0.0, 50.0, 10.0)
rolling_30 = st.sidebar.number_input("Rolling 30", 0.0, 50.0, 10.0)

# ---------------- FILTERING ----------------
if df is not None:
    min_year = int(df["Year"].min())
    max_year = int(df["Year"].max())

    year_range = st.sidebar.slider(
        "Filter Year",
        min_year, max_year,
        (min_year, max_year)
    )

    month_filter = st.sidebar.multiselect(
        "Filter Months",
        options=sorted(df["Month"].unique()),
        default=sorted(df["Month"].unique())
    )

    filtered_df = df[
        (df["Year"].between(year_range[0], year_range[1])) &
        (df["Month"].isin(month_filter))
    ]
else:
    filtered_df = None

# ---------------- PREDICTION ----------------
st.subheader("📊 Prediction")

input_data = pd.DataFrame({
    "Year": [year],
    "Month": [month],
    "Day": [day],
    "Temp_Range": [temp_range],
    "Rolling_7": [rolling_7],
    "Rolling_30": [rolling_30]
})

input_data = input_data[features]

if st.button("🚀 Predict Temperature"):
    pred = model.predict(input_data)[0]
    st.success(f"🌡 Predicted Temperature: {round(pred,2)} °C")

# ---------------- HEATMAP ----------------
st.subheader("🔥 Interactive Heatmap")

if filtered_df is not None:
    pivot = filtered_df.pivot_table(
        values="Land_Ocean_Temp",
        index="Year",
        columns="Month"
    )

    fig = px.imshow(
        pivot,
        labels=dict(x="Month", y="Year", color="Temp"),
        aspect="auto"
    )

    st.plotly_chart(fig, use_container_width=True)

# ---------------- LINE GRAPH ----------------
st.subheader("📈 Temperature Trend")

if filtered_df is not None:
    fig = px.line(
        filtered_df,
        x="Year",
        y="Land_Ocean_Temp",
        color="Month"
    )

    st.plotly_chart(fig, use_container_width=True)

# ---------------- ANIMATED GRAPH ----------------
st.subheader("🎞️ Animated Climate Change")

if filtered_df is not None:
    fig = px.line(
        filtered_df,
        x="Month",
        y="Land_Ocean_Temp",
        animation_frame="Year",
        range_y=[
            filtered_df["Land_Ocean_Temp"].min(),
            filtered_df["Land_Ocean_Temp"].max()
        ]
    )

    st.plotly_chart(fig, use_container_width=True)

# ---------------- HISTOGRAM ----------------
st.subheader("📊 Temperature Distribution")

if filtered_df is not None:
    fig = px.histogram(filtered_df, x="Land_Ocean_Temp", nbins=30)
    st.plotly_chart(fig, use_container_width=True)

# ---------------- ANOMALY ----------------
st.subheader("⚠️ Anomaly Detection")

if filtered_df is not None:
    threshold = filtered_df["Land_Ocean_Temp"].mean() + 2 * filtered_df["Land_Ocean_Temp"].std()
    anomalies = filtered_df[filtered_df["Land_Ocean_Temp"] > threshold]

    col1, col2 = st.columns(2)
    col1.metric("Threshold", round(threshold,2))
    col2.metric("Anomalies", len(anomalies))

# ---------------- PDF ----------------
def create_pdf(pred):
    doc = SimpleDocTemplate("report.pdf")
    styles = getSampleStyleSheet()

    content = []
    content.append(Paragraph("Climate Prediction Report", styles["Title"]))
    content.append(Paragraph(f"Predicted Temperature: {round(pred,2)} °C", styles["Normal"]))

    doc.build(content)

st.subheader("📄 Report")

if st.button("Generate Report"):
    pred = model.predict(input_data)[0]
    create_pdf(pred)

    with open("report.pdf", "rb") as f:
        st.download_button("⬇ Download PDF", f, file_name="report.pdf")
