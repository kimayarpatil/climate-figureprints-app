import streamlit as st
import pandas as pd
import numpy as np
import pickle
import plotly.express as px
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

st.set_page_config(page_title="Climate AI Dashboard", layout="wide")

# ---------------- TITLE ----------------
st.title("🌍 Climate Change Analysis Dashboard")
st.markdown("### 📊 Visualizing Global Temperature Trends (1880 - 2025)")

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
    except:
        # fallback dataset
        dates = pd.date_range("1880-01-01", periods=1000)
        df = pd.DataFrame({
            "Year": dates.year,
            "Month": dates.month,
            "Temp": np.random.normal(15, 3, 1000)
        })
    return df

df = load_data()

# ---------------- DATA CHECK ----------------
st.sidebar.write("📌 Data Info")
st.sidebar.write("Min Year:", int(df["Year"].min()))
st.sidebar.write("Max Year:", int(df["Year"].max()))

# ---------------- FILTERS ----------------
st.sidebar.header("⚙️ Filters")

start_year = st.sidebar.slider("Start Year", int(df["Year"].min()), int(df["Year"].max()), 2000)
end_year = st.sidebar.slider("End Year", int(df["Year"].min()), int(df["Year"].max()), 2025)

filtered_df = df[(df["Year"] >= start_year) & (df["Year"] <= end_year)]

# ---------------- INFO TEXT ----------------
st.markdown(f"""
### 📖 Insights
- This dashboard analyzes temperature trends between **{start_year} and {end_year}**
- Helps detect **climate change patterns**
- Identifies **temperature anomalies**
- Supports **AI-based prediction**
""")

# ---------------- PREDICTION ----------------
st.subheader("📊 AI Prediction")

col1, col2 = st.columns(2)

with col1:
    year = st.number_input("Year", 1880, 2100, 2025)
    month = st.slider("Month", 1, 12, 6)

with col2:
    temp_range = st.number_input("Temp Range", 0.0, 50.0, 10.0)
    rolling_7 = st.number_input("Rolling 7", 0.0, 50.0, 10.0)
    rolling_30 = st.number_input("Rolling 30", 0.0, 50.0, 10.0)

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
    if st.button("🚀 Predict Temperature"):
        pred = model.predict(input_data)[0]
        st.success(f"🌡 Predicted Temperature: {round(pred,2)} °C")
else:
    st.warning("Model not loaded (Demo Mode)")

# ---------------- HEATMAP ----------------
st.subheader("🔥 Monthly Temperature Heatmap")

heatmap_data = filtered_df.pivot_table(
    values="Temp",
    index="Month",
    columns="Year",
    aggfunc="mean"
)

fig_heatmap = px.imshow(heatmap_data, color_continuous_scale="hot", aspect="auto")
st.plotly_chart(fig_heatmap, use_container_width=True)

st.markdown("👉 This heatmap shows how temperature varies across months and years.")

# ---------------- TREND ----------------
st.subheader("📈 Temperature Trend Over Time")

fig_trend = px.line(filtered_df, x=filtered_df.index, y="Temp")
st.plotly_chart(fig_trend, use_container_width=True)

st.markdown("👉 Upward trend indicates global warming patterns.")

# ---------------- ANIMATION ----------------
st.subheader("🎞️ Climate Change Animation")

fig_anim = px.scatter(
    filtered_df,
    x="Month",
    y="Temp",
    animation_frame="Year",
    color="Temp",
    size="Temp"
)

st.plotly_chart(fig_anim, use_container_width=True)

# ---------------- DISTRIBUTION ----------------
st.subheader("📊 Temperature Distribution")

fig_hist = px.histogram(filtered_df, x="Temp", nbins=30)
st.plotly_chart(fig_hist, use_container_width=True)

st.markdown("👉 Distribution helps understand variation and spread of temperatures.")

# ---------------- ANOMALY ----------------
st.subheader("⚠️ Anomaly Detection")

mean_temp = filtered_df["Temp"].mean()
std_temp = filtered_df["Temp"].std()
threshold = mean_temp + 2 * std_temp

anomalies = filtered_df[filtered_df["Temp"] > threshold]

st.write("Threshold:", round(threshold,2))
st.write("Anomalies Found:", len(anomalies))

fig_anomaly = px.scatter(
    filtered_df,
    x=filtered_df.index,
    y="Temp",
    color=filtered_df["Temp"] > threshold
)

st.plotly_chart(fig_anomaly, use_container_width=True)

st.markdown("👉 Points above threshold are considered extreme temperature events.")

# ---------------- PDF ----------------
st.subheader("📄 Download Report")

def create_pdf(pred):
    doc = SimpleDocTemplate("report.pdf")
    styles = getSampleStyleSheet()

    content = []
    content.append(Paragraph("Climate Report", styles["Title"]))
    content.append(Paragraph(f"Predicted Temperature: {round(pred,2)} °C", styles["Normal"]))

    doc.build(content)

if st.button("Generate Report"):
    if model:
        pred = model.predict(input_data)[0]
    else:
        pred = np.mean(filtered_df["Temp"])

    create_pdf(pred)

    with open("report.pdf", "rb") as f:
        st.download_button("Download PDF", f, "report.pdf")
