import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import pickle
import io
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="Climate AI Dashboard", layout="wide")

st.title("🌍 Climate AI Dashboard")
st.markdown("### AI-powered climate monitoring, prediction & insights")

# -----------------------------
# LOAD MODEL
# -----------------------------
try:
    model = pickle.load(open("climate_model1.pkl", "rb"))
except:
    model = None

# -----------------------------
# LOAD / GENERATE DATA
# -----------------------------
@st.cache_data
def load_data():
    dates = pd.date_range(start="1880-01-01", end="2025-12-01", freq="M")

    df = pd.DataFrame({
        "Date": dates,
        "Year": dates.year,
        "Month": dates.month,
        "Temp": np.random.normal(15, 5, len(dates)),
        "CO2": np.linspace(280, 420, len(dates)) + np.random.normal(0, 5, len(dates)),
        "Sea_Level": np.linspace(0, 50, len(dates)) + np.random.normal(0, 2, len(dates)),
        "Precip": np.random.normal(100, 20, len(dates)),
        "Region": np.random.choice(["Global", "Asia", "Europe", "Africa"], len(dates))
    })

    # Climate Risk (important for animation)
    df["Climate_Risk"] = (
        (df["Temp"] - df["Temp"].min()) * 2 +
        (df["CO2"] - df["CO2"].min()) * 0.1 +
        (df["Sea_Level"] - df["Sea_Level"].min()) * 0.5
    )

    df["Climate_Risk"] = np.clip(df["Climate_Risk"], 1, 100)

    # Anomaly detection
    df["Anomaly"] = np.where(
        df["Temp"] > df["Temp"].mean() + 2 * df["Temp"].std(),
        1, 0
    )

    return df

df = load_data()

# -----------------------------
# SIDEBAR
# -----------------------------
st.sidebar.header("⚙️ Filters")

year_range = st.sidebar.slider(
    "Year Range",
    int(df["Year"].min()),
    int(df["Year"].max()),
    (2000, 2025)
)

region = st.sidebar.multiselect(
    "Region",
    df["Region"].unique(),
    default=list(df["Region"].unique())
)

selected_year = st.sidebar.selectbox(
    "Select Year for Simulation",
    sorted(df["Year"].unique()),
    index=len(df["Year"].unique()) - 1
)

# -----------------------------
# FILTER DATA
# -----------------------------
filtered_df = df[
    (df["Year"] >= year_range[0]) &
    (df["Year"] <= year_range[1]) &
    (df["Region"].isin(region))
].copy()

filtered_df = filtered_df.sort_values("Date")

if filtered_df.empty:
    st.error("No data available")
    st.stop()

# -----------------------------
# METRICS
# -----------------------------
st.subheader("📊 Key Climate Indicators")

col1, col2, col3 = st.columns(3)

col1.metric("🌡 Avg Temp", round(filtered_df["Temp"].mean(), 2))
col2.metric("🌫 CO2", round(filtered_df["CO2"].mean(), 2))
col3.metric("🌊 Sea Level", round(filtered_df["Sea_Level"].mean(), 2))

# -----------------------------
# TEXT INSIGHTS
# -----------------------------
st.markdown("### 📌 Insights")
st.write(f"""
- Temperature is showing a **gradual increasing trend**
- CO2 levels are **strongly correlated with temperature rise**
- Sea level rise indicates **long-term climate impact**
- Detected anomalies: **{filtered_df['Anomaly'].sum()} events**
""")

# -----------------------------
# PREDICTION
# -----------------------------
st.subheader("🤖 Climate Prediction")

temp_input = st.number_input("Temperature", value=20.0)
co2_input = st.number_input("CO2", value=400.0)

if st.button("Predict"):
    if model:
        pred = model.predict([[temp_input, co2_input]])[0]
        st.success(f"Prediction: {pred}")
    else:
        st.warning("Model not loaded")

# -----------------------------
# TEMPERATURE TREND
# -----------------------------
st.subheader("📈 Temperature Trend")

fig1 = px.line(filtered_df, x="Date", y="Temp")
st.plotly_chart(fig1, use_container_width=True)

# -----------------------------
# HEATMAP
# -----------------------------
st.subheader("🔥 Correlation Heatmap")

corr = filtered_df[["Temp", "CO2", "Sea_Level", "Precip"]].corr()

fig2 = px.imshow(corr, text_auto=True)
st.plotly_chart(fig2, use_container_width=True)

# -----------------------------
# DISTRIBUTION
# -----------------------------
st.subheader("📊 Temperature Distribution")

fig3 = px.histogram(filtered_df, x="Temp", nbins=30)
st.plotly_chart(fig3, use_container_width=True)

# -----------------------------
# ANOMALY DETECTION
# -----------------------------
st.subheader("⚠️ Anomaly Detection")

fig4 = px.scatter(
    filtered_df,
    x="Date",
    y="Temp",
    color=filtered_df["Anomaly"].astype(str)
)

st.plotly_chart(fig4, use_container_width=True)

# -----------------------------
# REGION ANALYSIS
# -----------------------------
st.subheader("🌍 Region Analysis")

region_avg = filtered_df.groupby("Region")["Temp"].mean().reset_index()

fig5 = px.bar(region_avg, x="Region", y="Temp", color="Temp")
st.plotly_chart(fig5, use_container_width=True)

# -----------------------------
# 🎞️ REAL-TIME CLIMATE SIMULATOR (FIXED)
# -----------------------------
st.subheader("🎞️ Real-Time Climate Simulator")

year_data = df[df["Year"] == selected_year].copy()

# CLEAN DATA (CRITICAL FIX)
year_data["Date"] = pd.to_datetime(year_data["Date"], errors="coerce")
year_data["Month"] = year_data["Date"].dt.month.astype(str)

year_data["Temp"] = pd.to_numeric(year_data["Temp"], errors="coerce")
year_data["Climate_Risk"] = pd.to_numeric(year_data["Climate_Risk"], errors="coerce")

year_data = year_data.dropna(subset=["Date", "Temp", "Climate_Risk", "Month"])
year_data["Climate_Risk"] = np.clip(year_data["Climate_Risk"], 1, 100)

if year_data.empty:
    st.warning("No data for selected year")
else:
    fig6 = px.scatter(
        year_data.tail(24),
        x="Date",
        y="Temp",
        animation_frame="Month",
        size="Climate_Risk",
        color="Climate_Risk",
        range_color=[0, 100],
        title=f"Climate Evolution: {selected_year}"
    )

    st.plotly_chart(fig6, use_container_width=True)

# -----------------------------
# PDF REPORT
# -----------------------------
st.subheader("📄 Download Report")

if st.button("Generate PDF"):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    content = []

    content.append(Paragraph("Climate Report", styles["Title"]))
    content.append(Spacer(1, 10))

    table_data = [
        ["Metric", "Value"],
        ["Avg Temp", str(round(filtered_df["Temp"].mean(), 2))],
        ["CO2", str(round(filtered_df["CO2"].mean(), 2))],
        ["Sea Level", str(round(filtered_df["Sea_Level"].mean(), 2))]
    ]

    content.append(Table(table_data))

    doc.build(content)

    st.download_button("Download PDF", buffer.getvalue(), "report.pdf")
