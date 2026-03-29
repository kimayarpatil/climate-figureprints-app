import streamlit as st
import pandas as pd
import numpy as np
import pickle
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

# ---------------- LOAD ----------------
model = pickle.load(open("climate_model1.pkl", "rb"))
features = pickle.load(open("features.pkl", "rb"))

st.set_page_config(page_title="Climate Predictor", layout="wide")
st.title("🌍 Climate Temperature Dashboard")

# ---------------- SIDEBAR INPUT ----------------
st.sidebar.header("User Input")

year = st.sidebar.number_input("Year", 2000, 2100, 2025)
month = st.sidebar.slider("Month", 1, 12, 6)
day = 15

temp_range = st.sidebar.number_input("Temp Range", 0.0, 50.0, 10.0)
rolling_7 = st.sidebar.number_input("Rolling 7", 0.0, 50.0, 10.0)
rolling_30 = st.sidebar.number_input("Rolling 30", 0.0, 50.0, 10.0)

# ---------------- INPUT DATA ----------------
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
if st.button("🚀 Predict Temperature"):
    pred = model.predict(input_data)[0]
    st.success(f"🌡 Predicted Temperature: {round(pred,2)} °C")

# ---------------- GRAPH SECTION ----------------
st.subheader("📈 Temperature Trend (Sample Data)")

# Dummy data for visualization
dates = pd.date_range(start="2000-01-01", periods=100)
temps = np.random.normal(15, 2, 100)

fig = plt.figure()
plt.plot(dates, temps)
plt.xlabel("Date")
plt.ylabel("Temperature")
plt.title("Temperature Trend")
st.pyplot(fig)

# ---------------- FEATURE IMPORTANCE ----------------
st.subheader("📊 Feature Importance")

importance = model.feature_importances_

fig2 = plt.figure()
plt.bar(features, importance)
plt.xticks(rotation=45)
st.pyplot(fig2)

# ---------------- ANOMALY DETECTION ----------------
st.subheader("⚠️ Anomaly Detection")

threshold = np.mean(temps) + 2*np.std(temps)
anomalies = temps > threshold

st.write("Anomaly Threshold:", round(threshold,2))
st.write("Detected Anomalies:", np.sum(anomalies))

# ---------------- PDF REPORT ----------------
def create_pdf(pred):
    doc = SimpleDocTemplate("report.pdf")
    styles = getSampleStyleSheet()

    content = []
    content.append(Paragraph("Climate Prediction Report", styles["Title"]))
    content.append(Paragraph(f"Predicted Temperature: {round(pred,2)} °C", styles["Normal"]))

    doc.build(content)

if st.button("📄 Download Report"):
    pred = model.predict(input_data)[0]
    create_pdf(pred)

    with open("report.pdf", "rb") as f:
        st.download_button("Download PDF", f, file_name="report.pdf")
