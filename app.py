import streamlit as st
import pandas as pd
import numpy as np
import pickle
import plotly.express as px
import plotly.graph_objects as go
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

st.set_page_config(page_title="Climate AI Dashboard", layout="wide")

st.title("🌍 Climate AI Dashboard")

# ---------------- LOAD MODEL ----------------
try:
    model = pickle.load(open("climate_model1.pkl", "rb"))
    features = pickle.load(open("features.pkl", "rb"))
except:
    model = None
    features = ["Year","Month","Day","Temp_Range","Rolling_7","Rolling_30"]

# ---------------- LOAD DATA ----------------
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("your_dataset.csv")
        return df
    except:
        # ✅ fallback synthetic dataset
        dates = pd.date_range("2000-01-01", periods=500)
        df = pd.DataFrame({
            "Year": dates.year,
            "Month": dates.month,
            "Temp": np.random.normal(15, 5, 500)
        })
        return df

df = load_data()

# ---------------- SIDEBAR ----------------
st.sidebar.header("⚙️ Input + Filters")

year = st.sidebar.slider("Year", int(df["Year"].min()), int(df["Year"].max()), int(df["Year"].max()))
month = st.sidebar.slider("Month", 1, 12, 6)

temp_range = st.sidebar.number_input("Temp Range", 0.0, 50.0, 10.0)
rolling_7 = st.sidebar.number_input("Rolling 7", 0.0, 50.0, 10.0)
rolling_30 = st.sidebar.number_input("Rolling 30", 0.0, 50.0, 10.0)

# ---------------- FILTER ----------------
filtered_df = df[(df["Year"] <= year) & (df["Month"] <= month)]

# ---------------- PREDICTION ----------------
st.subheader("📊 Prediction")

input_data = pd.DataFrame({
    "Year": [year],
    "Month": [month],
    "Day": [15],
    "Temp_Range": [temp_range],
    "Rolling_7": [rolling_7],
    "Rolling_30": [rolling_30]
})

input_data = input_data[features]

if model:
    if st.button("🚀 Predict"):
        pred = model.predict(input_data)[0]
        st.success(f"🌡 Predicted Temperature: {round(pred,2)} °C")
else:
    st.warning("Model not loaded - showing demo mode")

# ---------------- HEATMAP ----------------
st.subheader("🔥 Interactive Heatmap")

heatmap_data = filtered_df.pivot_table(
    values="Temp",
    index="Month",
    columns="Year",
    aggfunc="mean"
)

fig_heatmap = px.imshow(
    heatmap_data,
    color_continuous_scale="hot",
    aspect="auto"
)

st.plotly_chart(fig_heatmap, use_container_width=True)

# ---------------- TREND GRAPH ----------------
st.subheader("📈 Temperature Trend")

fig_trend = px.line(
    filtered_df,
    x=filtered_df.index,
    y="Temp",
    title="Temperature Trend"
)

st.plotly_chart(fig_trend, use_container_width=True)

# ---------------- ANIMATED GRAPH ----------------
st.subheader("🎞️ Animated Climate Change")

fig_anim = px.scatter(
    df,
    x="Month",
    y="Temp",
    animation_frame="Year",
    size="Temp",
    color="Temp"
)

st.plotly_chart(fig_anim, use_container_width=True)

# ---------------- DISTRIBUTION ----------------
st.subheader("📊 Temperature Distribution")

fig_hist = px.histogram(
    filtered_df,
    x="Temp",
    nbins=30
)

st.plotly_chart(fig_hist, use_container_width=True)

# ---------------- ANOMALY ----------------
st.subheader("⚠️ Anomaly Detection")

mean_temp = filtered_df["Temp"].mean()
std_temp = filtered_df["Temp"].std()

threshold = mean_temp + 2 * std_temp
anomalies = filtered_df[filtered_df["Temp"] > threshold]

st.write("Threshold:", round(threshold,2))
st.write("Anomalies Count:", len(anomalies))

fig_anomaly = px.scatter(
    filtered_df,
    x=filtered_df.index,
    y="Temp",
    color=filtered_df["Temp"] > threshold
)

st.plotly_chart(fig_anomaly, use_container_width=True)

# ---------------- PDF ----------------
st.subheader("📄 Report")

def create_pdf(pred):
    doc = SimpleDocTemplate("report.pdf")
    styles = getSampleStyleSheet()
    content = []

    content.append(Paragraph("Climate Report", styles["Title"]))
    content.append(Paragraph(f"Predicted Temp: {round(pred,2)} °C", styles["Normal"]))

    doc.build(content)

if st.button("Generate Report"):
    if model:
        pred = model.predict(input_data)[0]
    else:
        pred = np.mean(filtered_df["Temp"])

    create_pdf(pred)

    with open("report.pdf", "rb") as f:
        st.download_button("Download PDF", f, "report.pdf")
