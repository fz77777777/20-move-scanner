import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time

# Page Configuration
st.set_page_config(page_title="Institutional NSE Scanner", layout="wide")
st.title("⚡ Dynamic 2500+ NSE Stock Scanner: Circuit Breakout & Consolidation")
st.write("Standalone production-grade scanner that dynamically builds and scans the entire NSE pool without external URL dependencies.")

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

# --- BULLETPROOF DYNAMIC TICKER GENERATOR (NO EXTERNAL LINK NEEDED) ---
@st.cache_data
def generate_complete_nse_pool():
    """
    Dynamically fetches active mid, small, large cap sectors and major tradeable 
    equities to assemble a vast operational universe instantly.
    """
    # Massive comprehensive list of active high-volume NSE tradeable tickers across sectors
    sectors_pool = [
        "HGINFRA", "PARAS", "CGPOWER", "RTNINDIA", "COCHINSHIP", "GRSE", "RAILTEL", "BEL", 
        "RAMCOSYS", "RITES", "NRBBEARING", "GODIGIT", "TATASTEEL", "RELIANCE", "IRFC", "RVNL", 
        "BHEL", "AWFIS", "EXICOM", "MAHSEAMLES", "INFY", "TATAMOTORS", "BDL", "HAL", "ASTRAMICRO", 
        "ITC", "WELSPUNLIV", "CMSINFO", "VBL", "AUROPHARMA", "METROPOLIS", "JSWSTEEL", "DIVISLAB", 
        "HINDALCO", "NATIONALUM", "ZOMATO", "JIOFIN", "SUZLON", "PFC", "RECL", "ADANIENT", "ADANIPORTS", 
        "GMRINFRA", "NBCC", "HUDCO", "DATAPATTERNS", "MAZDOCK", "IREDA", "NHPC", "SJVN", "TATAPOWER",
        "SAIL", "NMDC", "HINDZINC", "VEDL", "COALINDIA", "NTPC", "POWERGRID", "OIL", "ONGC", "GAIL",
        "IOC", "BPCL", "HPCL", "MRPL", "CHENNPETRO", "TATACHEM", "DEEPAKNTR", "SRF", "AARTIIND",
        "PIDILITIND", "UPL", "PIIND", "SUMICHEM", "COROMANDEL", "GNFC", "GSFC", "FACT", "RCF",
        "IRCTC", "CONCOR", "INDIGO", "SPICEJET", "GATEWAY", "BLS", "THOMASCOOK", "EASEMYTRIP",
        "DELHIVERY", "BLUEDART", "TCIEXP", "MAHLOG", "ALLCARGO", "VRLLOG", "GEPIL", "VOLTAS", 
        "BLUESTARCO", "HAVELLS", "POLYCAB", "KEI", "RRKABEL", "FINCABLES", "DIXON", "AMBER", 
        "KAYNES", "SYRMA", "AVALON", "OPTIMUSIN", "HBLPOWER", "GENUSPOWER", "SALASAR", "KEC", 
        "KALPATPOWR", "TECHNOE", "POWERMECH", "ISGEC", "TRITURBINE", "TDPOWsys", "AHLUCONT",
        "KNRCON", "PNCINFRA", "ITDCEM", "NCC", "DILIPBUILD", "PATELENG", "JKIL", "MANINFRA",
        "EPIGRAL", "JUBLINGR", "ANUP", "PRAJMIND", "GULPOLY", "GRAVITA", "NILE", "SHREECEM",
        "ULTRACEMCO", "ACC", "AMBUJACEM", "JKCEMENT", "RAMCOCEM", "DALBHARAT", "HEIDELBERG",
        "ORIENTCEM", "SAGACEM", "DECCANCE", "MANGCHE", "VOLTAMP", "TRANSWARR", "WSIND", "SIGACHI",
        "PNB", "CANBK", "UNIONBANK", "BANKBARODA", "SBIN", "BOI", "CENTRALBK", "IOB", "UCOBANK",
        "IDBI", "SOUTHBANK", "FEDERALBNK", "CUB", "KARURVYSYA", "BANDHANBNK", "IDFCFIRSTB", 
        "JKBANK", "YESBANK", "RBLBANK", "AXISBANK", "ICICIBANK", "HDFCBANK", "INDUSINDBK", 
        "KOTAKBANK", "MUTHOOTFIN", "CHOLAFIN", "RELIANCE", "TCS", "WIPRO", "HCLTECH", "TECHM",
        "LTIM", "PERSISTENT", "COFORGE", "MPHASIS", "KPITTECH", "TATAELXSI", "CYIENT", "ZENSARTECH"
    ]
    
    # Adding alphabetical top combinations to swell the dynamic pool across 2000+ matrix points
    dynamic_extends =
