import streamlit as st
import pandas as pd
import numpy as np
import pickle
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="Climate AI Dashboard", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- CUSTOM CSS ----------------
st.markdown("""
<style>
    .main-header {font-size: 3rem; font-weight: bold; color: #1f77b4;}
    .metric-card {background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                  padding: 1rem; border-radius: 10px; color: white;}
</style>
""", unsafe_allow_html=True)

# ---------------- TITLE ----------------
st.markdown('<h1 class="main-header">🌍 Climate Change Analysis Dashboard</h1>', unsafe_allow_html=True)
st.markdown("### 📊 Visualizing Global Temperature Trends (1880 - 2025) | Powered by AI")

# ---------------- DATA LOADING ----------------
@st.cache_data
def load_real_data():
    """Load real climate data or generate realistic synthetic data"""
    try:
        # Try to load real NASA GISS data or similar
        url = "https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv"
        df = pd.read_csv(url, skiprows=1, na_values=['*****', '****', '***', ''])
        df = df.melt(id_vars=['Year'], var_name='Month', value_name='Temp')
        df['Month'] = df['Month'].str.extract('(\d+)').astype(int)
        df['Date'] = pd.to_datetime(df[['Year', 'Month']].assign(day=1))
        df = df.dropna()
        return df
    except:
        # Generate realistic synthetic climate data
        np.random.seed(42)
        years = np.arange(1880, 2026)
        n_months = len(years) * 12
        base_temp = 14.0
        trend = 0.008  # ~0.8°C per century
        
        temps = []
        for i, year in enumerate(years):
            seasonal = 10 * np.sin(2 * np.pi * np.arange(12) / 12)
            warming = trend * (year - 1880)
            noise = np.random.normal(0, 0.8, 12)
            monthly_temps = base_temp + seasonal + warming + noise
            temps.extend(monthly_temps)
        
        df = pd.DataFrame({
            'Date': pd.date_range('1880-01-01', periods=n_months, freq='MS'),
            'Year': np.repeat(years, 12),
            'Month': np.tile(np.arange(1,13), len(years)),
            'Temp': temps
        })
        return df

df = load_real_data()

# ---------------- MODEL LOADING ----------------
@st.cache_resource
def load_model():
    """Load climate prediction model with fallback"""
    try:
        model = pickle.load(open("climate_model1.pkl", "rb"))
        with open("features.pkl", "rb") as f:
            features = pickle.load(f)
        return model, features
    except:
        return None, ["Year", "Month", "Temp_Range", "Rolling_7", "Rolling_30"]

model, features = load_model()

# ---------------- SIDEBAR METRICS ----------------
st.sidebar.markdown("## 📊 Quick Stats")
col1, col2, col3, col4 = st.sidebar.columns(4)
col1.metric("Total Records", len(df))
col2.metric("Temp Range", f"{df['Temp'].min():.1f}°C - {df['Temp'].max():.1f}°C")
col3.metric("Global Avg", f"{df['Temp'].mean():.2f}°C")
col4.metric("Trend", f"{df['Temp'].tail(120).mean() - df['Temp'].head(120).mean():+.2f}°C")

# ---------------- FILTERS ----------------
st.sidebar.header("🔍 Filters")
start_year = st.sidebar.slider("Start Year", int(df["Year"].min()), 2020, 2000)
end_year = st.sidebar.slider("End Year", start_year, int(df["Year"].max()), 2025)
show_anomalies = st.sidebar.checkbox("Highlight Anomalies", True)

filtered_df = df[(df["Year"] >= start_year) & (df["Year"] <= end_year)].copy()
filtered_df['Rolling_7'] = filtered_df['Temp'].rolling(7, min_periods=1).mean()
filtered_df['Rolling_30'] = filtered_df['Temp'].rolling(30, min_periods=1).mean()
filtered_df['Temp_Range'] = filtered_df['Temp'].rolling(12).std().fillna(0)

# ---------------- MAIN DASHBOARD ----------------
tab1, tab2, tab3, tab4 = st.tabs(["📈 Overview", "🔮 Predictions", "🔥 Heatmaps", "⚠️ Anomalies"])

with tab1:
    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Avg Temp</h3>
            <h2>{filtered_df['Temp'].mean():.2f}°C</h2>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        trend = filtered_df['Temp'].tail(60).mean() - filtered_df['Temp'].head(60).mean()
        st.markdown(f"""
        <div class="metric-card">
            <h3>5Y Trend</h3>
            <h2>{trend:+.2f}°C</h2>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        anomalies = filtered_df[filtered_df['Temp'] > filtered_df['Temp'].mean() + 2*filtered_df['Temp'].std()]
        st.markdown(f"""
        <div class="metric-card">
            <h3>Anomalies</h3>
            <h2>{len(anomalies)}</h2>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Records</h3>
            <h2>{len(filtered_df):,}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    # Main Trend Chart
    fig_trend = px.line(filtered_df, x='Date', y='Temp', 
                       title=f"🌡️ Temperature Trend ({start_year}-{end_year})",
                       labels={'Temp': 'Temperature (°C)', 'Date': 'Date'})
    fig_trend.update_traces(line=dict(color='#ff6b6b', width=3))
    st.plotly_chart(fig_trend, use_container_width=True)

with tab2:
    st.header("🤖 AI Temperature Prediction")
    
    col1, col2 = st.columns(2)
    with col1:
        pred_year = st.number_input("📅 Year", 2025, 2100, 2026)
        pred_month = st.slider("📅 Month", 1, 12, 7)
    
    with col2:
        if len(filtered_df) > 0:
            default_range = filtered_df['Temp_Range'].mean()
            default_7 = filtered_df['Rolling_7'].mean()
            default_30 = filtered_df['Rolling_30'].mean()
        else:
            default_range = 2.0
            default_7 = 15.0
            default_30 = 15.0
            
        temp_range = st.number_input("📊 Temp Range (σ)", 0.0, 10.0, default_range)
        rolling_7 = st.number_input("📈 7-day Rolling", 0.0, 50.0, default_7)
        rolling_30 = st.number_input("📈 30-day Rolling", 0.0, 50.0, default_30)
    
    input_data = pd.DataFrame({
        "Year": [pred_year],
        "Month": [pred_month],
        "Day": [15],
        "Temp_Range": [temp_range],
        "Rolling_7": [rolling_7],
        "Rolling_30": [rolling_30]
    })[features]
    
    col1, col2 = st.columns([3,1])
    with col1:
        if st.button("🚀 Predict Future Temperature", type="primary"):
            if model:
                pred = model.predict(input_data)[0]
                st.success(f"### 🌡️ **Predicted Temperature: {pred:.2f}°C**")
                st.balloons()
            else:
                # Fallback prediction using trend
                base_temp = filtered_df['Temp'].tail(12).mean()
                trend_per_year = 0.02  # Estimated warming trend
                years_ahead = pred_year - filtered_df['Year'].max()
                pred = base_temp + trend_per_year * years_ahead
                st.info(f"### 🌡️ **Trend-based Prediction: {pred:.2f}°C**")
                st.caption("💡 Model unavailable - using linear trend extrapolation")
    
    with col2:
        if st.button("📊 Show Confidence"):
            if model:
                pred_proba = model.predict_proba(input_data)
                st.metric("Confidence", f"{max(pred_proba[0]):.1%}")

with tab3:
    # Enhanced Heatmap
    pivot_data = filtered_df.pivot_table(values="Temp", index="Month", columns="Year", aggfunc="mean")
    
    fig_heatmap = px.imshow(
        pivot_data, 
        color_continuous_scale="RdYlBu_r",
        title="🔥 Monthly Temperature Heatmap",
        aspect="auto"
    )
    fig_heatmap.update_layout(height=500)
    st.plotly_chart(fig_heatmap, use_container_width=True)

with tab4:
    # Anomaly Detection
    mean_temp = filtered_df["Temp"].mean()
    std_temp = filtered_df["Temp"].std()
    threshold = mean_temp + 2 * std_temp
    
    filtered_df['is_anomaly'] = filtered_df["Temp"] > threshold
    anomalies = filtered_df[filtered_df['is_anomaly']]
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Anomaly Threshold", f"{threshold:.2f}°C")
        st.metric("Anomalies Found", len(anomalies))
        st.metric("Anomaly Rate", f"{len(anomalies)/len(filtered_df)*100:.1f}%")
    
    with col2:
        fig_anomaly = px.scatter(
            filtered_df, x='Date', y='Temp',
            color='is_anomaly',
            title="⚠️ Temperature Anomalies",
            color_discrete_map={True: 'red', False: 'blue'}
        )
        fig_anomaly.add_hline(y=threshold, line_dash="dash", line_color="orange")
        st.plotly_chart(fig_anomaly, use_container_width=True)

# ---------------- REPORT GENERATION ----------------
st.sidebar.markdown("---")
st.sidebar.subheader("📄 Report")

def create_pdf_report(prediction=None):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=(8.5*inch, 11*inch))
    styles = getSampleStyleSheet()
    
    story = []
    story.append(Paragraph("Climate Change Analysis Report", styles['Title']))
    story.append(Spacer(1, 20))
    
    # Summary table
    data = [
        ['Metric', 'Value'],
        ['Period', f'{start_year}-{end_year}'],
        ['Avg Temperature', f'{filtered_df["Temp"].mean():.2f}°C'],
        ['Temperature Trend', f'{filtered_df["Temp"].tail(60).mean() - filtered_df["Temp"].head(60).mean():+.2f}°C'],
        ['Anomalies', str(len(anomalies))]
    ]
    
    if prediction:
        data.append(['AI Prediction', f'{prediction:.2f}°C'])
    
    table = Table(data)
    table.setStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 14),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-1), colors.beige),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ])
    story.append(table)
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

if st.sidebar.button("📥 Download Report", type="secondary"):
    pred = model.predict(input_data)[0] if model else filtered_df['Temp'].mean()
    pdf_bytes = create_pdf_report(pred)
    st.sidebar.download_button(
        "📄 Download PDF Report",
        pdf_bytes,
        "climate_report.pdf",
        "application/pdf"
    )

# Footer
st.markdown("---")
st.markdown("### 💡 Built with ❤️ using Streamlit + Plotly | Data: NASA GISS & Synthetic Climate Data")
