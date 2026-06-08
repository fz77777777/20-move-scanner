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

    # Core Matrix 2: Fetch Broad Market Equities [FIXED INCOMPLETE CODE HERE]
    try:
        url_total = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
        df_total = pd.read_csv(url_total)
        df_total.columns = [c.upper().strip() for c in df_total.columns]
        
        symbol_col = 'SYMBOL' if 'SYMBOL' in df_total.columns else df_total.columns[0]
        name_col = 'NAME OF COMPANY' if 'NAME OF COMPANY' in df_total.columns else df_total.columns[1]
        series_col = 'SERIES' if 'SERIES' in df_total.columns else None
        
        if series_col and series_col in df_total.columns:
            df_total = df_total[df_total[series_col].astype(str).str.upper().str.strip() == 'EQ']
            
        existing_symbols = {item['Symbol_YF'] for item in base_pool}
        
        for _, row in df_total.iterrows():
            ticker = str(row[symbol_col]).strip()
            if not ticker or ticker.lower() == 'symbol':
                continue
                
            yf_symbol = ticker + ".NS"
            if yf_symbol not in existing_symbols:
                base_pool.append({
                    'Symbol_YF': yf_symbol,
                    'Company Name': row[name_col] if name_col in df_total.columns else ticker
                })
            if len(base_pool) >= 2300: # Security cap
                break
    except Exception:
        pass
        
    return pd.DataFrame(base_pool)

master_universe = load_complete_nse_universe()
TICKER_LIST = master_universe['Symbol_YF'].tolist()
TICKER_MAP = dict(zip(master_universe['Symbol_YF'], master_universe['Company Name']))

st.sidebar.success(f"🎯 Total Equities Loaded: {len(TICKER_LIST)} Stocks")

# ==========================================
# ULTRA-FAST HIGH SPEED BATCH DOWNLOAD ENGINE
# ==========================================
@st.cache_data(ttl=1800)
def fetch_all_market_data_instantly(tickers, days_lookback):
    end_date = datetime.today().strftime('%Y-%m-%d')
    start_date = (datetime.today() - timedelta(days=days_lookback + 60)).strftime('%Y-%m-%d')
    df = yf.download(tickers, start=start_date, end=end_date, interval="1d", group_by='ticker', progress=False)
    return df

# ==========================================
# SCAN EXECUTION MATRIX
# ==========================================
if st.button("🚀 Run Complete 2000+ Stock Breakout Scan"):
    with st.spinner("Downloading full Indian market data nodes into local RAM memory..."):
        all_data = fetch_all_market_data_instantly(TICKER_LIST, lookback_days)
        
    st.write("⚙️ **Analyzing Technical Vectors (Circuit Breakout & Consolidation Range)...**")
    
    scanned_data_pool = []
    
    for ticker in TICKER_LIST:
        try:
            if len(TICKER_LIST) > 1:
                df = all_data[ticker].dropna(subset=['Close'])
            else:
                df = all_data.dropna(subset=['Close'])
                
            if len(df) < 25: 
                continue
                
            df = df.copy()
            df['Daily_Return'] = df['Close'].pct_change() * 100
            df['Avg_Vol_20'] = df['Volume'].rolling(window=20).mean()
            
            search_df = df.tail(lookback_days)
            circuit_days = search_df[search_df['Daily_Return'] >= min_move]
            
            if not circuit_days.empty:
                last_circuit_row = circuit_days.iloc[-1]
                circuit_date = circuit_days.index[-1]
                
                if pd.isna(last_circuit_row['Avg_Vol_20']) or last_circuit_row['Avg_Vol_20'] == 0:
                    continue
                    
                # 1. Volume Spurt Verification Check
                if last_circuit_row['Volume'] >= (last_circuit_row['Avg_Vol_20'] * volume_multiplier):
                    
                    # 2. Tight Range Consolidation Verification Check
                    recent_df = df.tail(consolidation_days)
                    if len(recent_df) >= consolidation_days:
                        max_close = recent_df['Close'].max()
                        min_close = recent_df['Close'].min()
                        
                        consolidation_range = ((max_close - min_close) / min_close) * 100
                        
                        if consolidation_range <= max_consolidation_allowed:
                            breakout_volume_mn = last_circuit_row['Volume'] / 1_000_000
                                
                            scanned_data_pool.append({
                                "Ticker Symbol": ticker.replace('.NS', ''),
                                "Company Name": TICKER_MAP.get(ticker, "Unknown"),
                                "Current Close Price": f"₹{round(df['Close'].iloc[-1], 2)}",
                                f"Breakout Date Context": circuit_date.strftime('%Y-%m-%d'),
                                "Move % on Breakout Day": f"{round(last_circuit_row['Daily_Return'], 2)}%",
                                "Breakout Day Vol": f"{round(breakout_volume_mn, 2)} M",
                                "Recent Consolidation Range": f"{round(consolidation_range, 2)}%"
                            })
        except Exception:
            continue
            
    # Display Results Engine
    if scanned_data_pool:
        final_df = pd.DataFrame(scanned_data_pool)
        st.success(f"🎯 **Scan Complete!** Identified **{len(final_df)} Alpha Setup Candidates** matching your layout parameters!")
        st.dataframe(final_df, use_container_width=True)
        
        # Plotly Candlestick Chart Render for priority lead matched stock
        priority_ticker = final_df.iloc[0]['Ticker Symbol'] + ".NS"
        try:
            chart_df = all_data[priority_ticker].dropna().tail(90)
            
            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=chart_df.index, open=chart_df['Open'], high=chart_df['High'], 
                low=chart_df['Low'], close=chart_df['Close'], name="Price Action"
            ))
            fig.update_layout(
                xaxis_rangeslider_visible=False, template="plotly_white", 
                height=500, title=f"📈 Chart Preview Context: {priority_ticker.replace('.NS','')}"
            )
            st.plotly_chart(fig, use_container_width=True)
        except Exception:
            pass
            
        csv = final_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export Results Array to CSV", csv, "breakout_setup_output.csv", "text/csv")
    else:
        st.warning("Pure market data spectrum me koi stock is selection parameter setup par fit nahi baitha. Sliders ko halka adjust karke dekhein.")
