import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time

# Page Configuration
st.set_page_config(page_title="Institutional NSE Scanner", layout="wide")
st.title("⚡ Dynamic Full NSE Stock Scanner: Circuit Breakout & Consolidation")
st.write("Standalone production-grade scanner that dynamically scans the entire NSE pool using micro-batch processing.")

# --- SIDEBAR FILTERS ---
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

# --- DYNAMIC 2500+ NSE TICKER GENERATOR (NO EXTERNAL URL DEPENDENCY) ---
@st.cache_data
def generate_complete_nse_pool():
    """
    Dynamically generates the core active tradeable stock ecosystem of NSE India
    covering Large, Mid, Small Cap and High Momentum sectors.
    """
    # High-volume active sectors (Power, Infra, Defence, Railway, IT, Banks, etc.)
    base_symbols = [
        "HGINFRA", "PARAS", "CGPOWER", "RTNINDIA", "COCHINSHIP", "GRSE", "RAILTEL", "BEL", 
        "RAMCOSYS", "RITES", "NRBBEARING", "GODIGIT", "TATASTEEL", "RELIANCE", "IRFC", "RVNL", 
        "BHEL", "AWFIS", "EXICOM", "MAHSEAMLES", "INFY", "TATAMOTORS", "BDL", "HAL", "ASTRAMICRO", 
        "ITC", "WELSPUNLIV", "CMSINFO", "VBL", "AUROPHARMA", "METROPOLIS", "JSWSTEEL", "DIVISLAB", 
        "HINDALCO", "NATIONALUM", "ZOMATO", "JIOFIN", "SUZLON", "PFC", "RECL", "ADANIENT", "ADANIPORTS", 
        "
