import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="20% Circuit Breakout Scanner",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ Full Market 20% Circuit Breakout & Consolidation Scanner")
st.write("Production-grade engine engineered to scan 2000+ NSE stocks in a single consolidated memory pass.")
st.write("---")

# ==========================================
# SIDEBAR CONTROL PANEL
# ==========================================
st.sidebar.header("🔍 Filter Parameters")

lookback_days = st.sidebar.selectbox(
    "Select Search Window (How many days ago?)",
    options=[30, 45, 60, 90],
    index=2
)

min_move = st.sidebar.slider(
    "Select Minimum Circuit/Sharp Move (%)", 
    min_value=10, max_value=20, value=14, step=1
)

volume_multiplier = st.sidebar.slider(
    "Volume Spurt Filter (X times of 20-day Avg Volume)", 
    min_value=1.0, max_value=10.0, value=1.5, step=0.5
)

consolidation_days = st.sidebar.slider(
    "Consolidation Period (Recent Days)", 
    min_value=3, max_value=20, value=5, step=1
)

max_consolidation_allowed = st.sidebar.slider(
    "Max Allowed Consolidation Band (%)",
    min_value=5.0, max_value=25.0, value=12.0, step=0.5
)

# ==========================================
# DYNAMIC 2000+ NSE TICKER ENGINE (FAST PATH)
# ==========================================
@st.cache_data(ttl=86400)
def load_complete_nse_universe():
    base_pool = []
    
    # Core Matrix 1: Fetch Nifty 500
    try:
        url_500 = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
        df_500 = pd.read_csv(url_500)
        df_500.columns = [c.upper().strip() for c in df_500.columns]
        symbol_col = 'SYMBOL' if 'SYMBOL' in df_500.columns else df_500.columns[2]
        company_col = 'COMPANY NAME' if 'COMPANY NAME' in df_500.columns else df_500.columns[0]

        for _, row in df_500.iterrows():
            base_pool.append({
                'Symbol_YF': str(row[symbol_col]).strip() + ".NS",
                'Company Name': row[company_col]
            })
    except Exception:
        pass

    # Core Matrix 2: Fetch Broad Market Equities
    try:
        url_total = "https://archives.nseindia
