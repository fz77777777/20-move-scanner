import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Page Configuration
st.set_page_config(page_title="Advanced Catalyst & Consolidation Scanner", layout="wide")
st.title("📊 Advanced Stock Scanner: Circuit Breakout & Consolidation (Full NSE)")
st.write("Scan entire 2500+ NSE market for historical sharp moves, volume expansion, and tight consolidation.")

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

# --- DYNAMIC 2500+ TICKER LOAD FROM PUBLIC REPOSITORY ---
@st.cache_data
def load_all_nse_tickers():
    try:
        # Fetching latest updated complete stock list of NSE dynamically
        url = "https://raw.githubusercontent.com/itsjustfaiz/NSE-Stocks-Ticker/main/nse_all_stocks.csv"
        # Fallback public raw asset containing all active NSE equities
        fallback_url = "https://raw.githubusercontent.com/shangb/NSE-equity-list/master/equity.csv"
        
        try:
            df_nse = pd.read_csv(url)
            ticker_col = [col for col in df_nse.columns if 'SYMBOL' in col.upper() or 'TICKER' in col.upper()][0]
            tickers = df_nse[ticker_col].dropna().tolist()
        except Exception:
            df_nse = pd.read_csv(fallback_url)
            tickers = df_nse['SYMBOL'].dropna().tolist()
            
        # Standardizing for yfinance data extraction format (adding .NS suffix)
        nse_tickers = [str(symbol).strip() + ".NS" for symbol in tickers if str(symbol).strip().isalnum()]
        return sorted(list(set(nse_tickers)))
    except Exception as e:
        # Ultimate fallback array if repository link fails temporarily
        return ["HGINFRA.NS", "PARAS.NS", "CGPOWER.NS", "RTNINDIA.NS", "COCHINSHIP.NS", "GRSE.NS", "RAILTEL.NS", "BEL.NS"]

with st.spinner("Loading 2500+ NSE Tickers database..."):
    tickers = load_all_nse_tickers()
st.sidebar.success(f"Loaded Total Active Stocks: {len(tickers)}")

# --- SCANNING LOGIC ---
def scan_stocks(ticker_list, min_move, vol_mult, cons_days, lookback, max_cons):
    scanned_data = []
    
    end_date = datetime.today()
    start_date = end_date - timedelta(days=lookback + 40) 
    
    # UI Elements for progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    total_tickers = len(ticker_list)
    
    for idx, ticker in enumerate(ticker_list):
        # Update progress and status on screen
        progress_bar.progress((idx + 1) / total_tickers)
        if idx % 50 == 0:
            status_text.text(f"Scanning {
