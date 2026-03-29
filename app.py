import streamlit as st
import pandas as pd
import numpy as np
import pickle
import matplotlib.pyplot as plt
import os
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Climate Dashboard", layout="wide")

# ---------------- CUSTOM CSS ----------------
st.markdown("""
<style>
.main {
    background-color: #0e1117;
}
.card {
    background-color: #1c1f26;
    padding: 20px;
    border-radius: 12px;
    box-shadow: 0px 4px 10px rgba(0,0,0,0.5);
}
h1, h2, h3 {
    color: #ffffff;
}
</style>
""", unsafe_allow_html=True)

st.title("🌍 Climate AI Dashboard")

# ---------------- LOAD MODEL ----------------
if not os.path.exists("climate_model1.pkl"):
    st.error("Model file missing")
    st.stop()

model = pickle.load(open("climate_model1.pkl", "rb"))
features = pickle.load(open("features.pkl", "rb"))

# ---------------- SIDEBAR ----------------
st.sidebar.header("⚙️ Input Parameters")

year = st.sidebar.number_input("Year", 2000, 2100, 2025)
month = st.sidebar.slider("Month", 1, 12, 6)
day = 15

temp_range = st.sidebar.number_input("Temp Range", 0.0, 50.0, 10.0)
rolling_7 = st.sidebar.number_input("Rolling 7", 0.0, 50.0, 10.0)
rolling_30 = st.sidebar.number_input("Rolling 30", 0.0, 50.0, 10.0)

# ---------------- INPUT ----------------
input_data = pd.DataFrame({
    "Year": [year],
    "Month": [month],
    "Day": [day],
    "Temp_Range": [temp_range],
    "Rolling_7": [rolling_7],
    "Rolling_30": [rolling_30]
})

input_data = input_data[features]

# ---------------- PREDICTION ----------------
st.subheader("📊 Prediction Overview")

col1, col2, col3 = st.columns(3)

if st.button("🚀 Predict"):
    pred = model.predict(input_data)[0]

    col1.metric("🌡 Temperature", f"{round(pred,2)} °C")
    col2.metric("📅 Year", year)
    col3.metric("📈 Trend", "Rising 🔥")

# ---------------- GRAPH ----------------
st.subheader("📈 Temperature Trend")

dates = pd.date_range(start="2000-01-01", periods=100)
temps = np.random.normal(15, 2, 100)

fig = plt.figure()
plt.plot(dates, temps)
plt.grid()
plt.title("Temperature Trend")
st.pyplot(fig)

# ---------------- FEATURE IMPORTANCE ----------------
st.subheader("📊 Feature Importance")

importance = model.feature_importances_

fig2 = plt.figure()
plt.bar(features, importance)
plt.xticks(rotation=45)
st.pyplot(fig2)

# ---------------- ANOMALY ----------------
st.subheader("⚠️ Anomaly Detection")

threshold = np.mean(temps) + 2*np.std(temps)
anomalies = temps > threshold

col4, col5 = st.columns(2)

col4.metric("Threshold", round(threshold,2))
col5.metric("Anomalies", int(np.sum(anomalies)))

# ---------------- PDF ----------------
def create_pdf(pred):
    doc = SimpleDocTemplate("report.pdf")
    styles = getSampleStyleSheet()

    content = []
    content.append(Paragraph("Climate Report", styles["Title"]))
    content.append(Paragraph(f"Predicted Temp: {round(pred,2)} °C", styles["Normal"]))

    doc.build(content)

st.subheader("📄 Report")

if st.button("Generate Report"):
    pred = model.predict(input_data)[0]
    create_pdf(pred)

    with open("report.pdf", "rb") as f:
        st.download_button("⬇ Download PDF", f)
