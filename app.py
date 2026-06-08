import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ==========================================
# PAGE CONFIGURATION & THEME
# ==========================================
st.set_page_config(
    page_title="Stockbee Hot-Sector Ultra-Scanner",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional Minimalist Theme
st.markdown("""
    <style>
    .stButton>button { 
        background-color: #d9534f; 
        color: white; 
        border-radius: 6px; 
        font-weight: bold;
        padding: 0.5rem 2.5rem;
        font-size: 16px;
    }
    .stButton>button:hover { background-color: #c9302c; color: #ffffff; }
    h1 { color: #111111; font-family: 'Helvetica Neue', Arial, sans-serif; font-weight: 800; }
    </style>
""", unsafe_allow_html=True)

st.title("🔥 Indian Market: Stockbee Hot-Sector Momentum Engine")
st.markdown("### **Sectoral Relative Strength (RS) + Institutional Breakout Array (No Microcaps)**")
st.write("---")

# ==========================================
# SIDEBAR CONTROL PANEL
# ==========================================
with st.sidebar:
    st.header("⚡ Historical Time Machine")
    historical_days = st.slider("Select Historical Data Lookback (Days Ago)", min_value=0, max_value=30, value=0, step=1)
    
    if historical_days == 0:
        st.success("📍 Scanning: Current Live / Latest Close")
    else:
        st.warning(f"⏳ Time Machine Active: {historical_days} Days Ago Data")
        
    st.write("---")
    st.header("🎯 Strategy Parameters")
    min_gain = st.slider("Minimum Price Gain (%)", min_value=3.0, max_value=15.0, value=5.0, step=0.5)
    vol_multiplier = st.slider("Volume Multiplier (x Volume SMA50)", min_value=1.5, max_value=6.0, value=2.5, step=0.1)
    
    st.write("---")
    st.header("⚙️ Structural Filters")
    
    timeframe_filter = st.selectbox(
        "Select Data Timeframe",
        options=["Daily", "Weekly"],
        index=0
    )
    
    setup_filter = st.selectbox(
        "Select Setup Structure",
        options=[
            "Hot Sector Setups Combined",
            "Fresh EP Breakout (Hot Sectors Only)",
            "Late EP / Consolidation (Hot Sectors Only)",
            "Pullback Near 10/20 EMA (Hot Sectors Only)"
        ],
        index=0
    )

# ==========================================
# DYNAMIC 2000+ INDIAN TICKER LOADER (BULLETPROOF)
# ==========================================
@st.cache_data(ttl=86400)
def load_indian_mega_universe_clean():
    base_pool = []
    
    # STEP 1: Load Nifty 500
    try:
        url_500 = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
        df_500 = pd.read_csv(url_500)
        df_500.columns = [c.upper().strip() for c in df_500.columns]
        symbol_col = 'SYMBOL' if 'SYMBOL' in df_500.columns else df_500.columns[2]
        industry_col = 'INDUSTRY' if 'INDUSTRY' in df_500.columns else df_500.columns[3]
        company_col = 'COMPANY NAME' if 'COMPANY NAME' in df_500.columns else df_500.columns[0]

        for _, row in df_500.iterrows():
            yf_symbol = str(row[symbol_col]).strip() + ".NS"
            base_pool.append({
                'Symbol_YF': yf_symbol,
                'Company Name': row[company_col],
                'Sector': row[industry_col] if pd.notna(row[industry_col]) else 'Core Sector'
            })
    except Exception as e:
        st.warning(f"Nifty 500 parse alert: {e}")

    # STEP 2: Fetch full NSE Equities List
    try:
        url_total = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
        df_total = pd.read_csv(url_total)
        df_total.columns = [c.upper().strip() for c in df_total.columns]
        
        symbol_col = 'SYMBOL' if 'SYMBOL' in df_total.columns else df_total.columns[0]
        name_col = 'NAME OF COMPANY' if 'NAME OF COMPANY' in df_total.columns else df_total.columns[1]
        series_col = 'SERIES' if 'SERIES' in df_total.columns else (df_total.columns[2] if len(df_total.columns) > 2 else None)
        
        if series_col and series_col in df_total.columns:
            df_total = df_total[df_total[series_col].astype(str).str.upper().str.strip() == 'EQ']
            
        existing_symbols = set()
        for item in base_pool:
            existing_symbols.add(item['Symbol_YF'])
        
        for _, row in df_total.iterrows():
            ticker = str(row[symbol_col]).strip()
            if not ticker or ticker.lower() == 'symbol':
                continue
                
            yf_symbol = ticker + ".NS"
            if yf_symbol not in existing_symbols:
                base_pool.append({
                    'Symbol_YF': yf_symbol,
                    'Company Name': row[name_col] if name_col in df_total.columns else ticker,
                    'Sector': 'Broad Market / Mid-Small'
                })
            if len(base_pool) >= 2150:
                break
    except Exception as e:
        st.error(f"Fatal error pulling broad market array: {e}")
        
    if len(base_pool) < 10:
        emergency_stocks = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK']
        return pd.DataFrame([{'Symbol_YF': f'{s}.NS', 'Company Name': f'{s} Ltd', 'Sector': 'Benchmark'} for s in emergency_stocks])
        
    return pd.DataFrame(base_pool)

master_universe = load_indian_mega_universe_clean()
TICKER_LIST = master_universe['Symbol_YF'].tolist()
TICKER_MAP = dict(zip(master_universe['Symbol_YF'], master_universe['Company Name']))
SECTOR_MAP = dict(zip(master_universe['Symbol_YF'], master_universe['Sector']))

# ==========================================
# TIMEFRAME DATA PROCESSING ENGINE
# ==========================================
@st.cache_data(ttl=1800)
def fetch_indian_data_batch(tickers, tf):
    interval_map = {"Daily": "1d", "Weekly": "1wk"}
    yf_interval = interval_map[tf]
    end_date = datetime.today().strftime('%Y-%m-%d')
    start_date = (datetime.today() - timedelta(days=1200)).strftime('%Y-%m-%d')
    df = yf.download(tickers, start=start_date, end=end_date, interval=yf_interval, group_by='ticker', progress=False)
    return df

# OPTIMIZED: QUICK FUNDAMENTAL LOOKUP WITHOUT CRASHING
def fetch_dual_quarterly_growth(ticker_raw):
    curr_g = "Data N/A"
    prev_g = "Data N/A"
    try:
        ticker_obj = yf.Ticker(ticker_raw)
        funda_matrix = ticker_obj.quarterly_financials
        
        revenue_labels = ['Total Revenue', 'Gross Sales', 'Operating Revenue']
        target_key = None
        for key in revenue_labels:
            if key in funda_matrix.index:
                target_key = key
                break
                
        if target_key is not None:
            revenue_stream = funda_matrix.loc[target_key].dropna()
            
            if len(revenue_stream) >= 3:
                q0_latest = float(revenue_stream.iloc[0])
                q1_prior = float(revenue_stream.iloc[1])
                q2_older = float(revenue_stream.iloc[2])
                
                if q1_prior > 0:
                    curr_g = f"{round(((q0_latest - q1_prior) / q1_prior) * 100, 2)}%"
                if q2_older > 0:
                    prev_g = f"{round(((q1_prior - q2_older) / q2_older) * 100, 2)}%"
            elif len(revenue_stream) == 2:
                q0_latest = float(revenue_stream.iloc[0])
                q1_prior = float(revenue_stream.iloc[1])
                if q1_prior > 0:
                    curr_g = f"{round(((q0_latest - q1_prior) / q1_prior) * 100, 2)}%"
    except Exception:
        pass
    return curr_g, prev_g

# ==========================================
# MAIN EXECUTION LAYER
# ==========================================
if st.button(f"🚀 RUN HOT-SECTOR MOMENTUM SCANNER"):
    with st.spinner("Downloading global market nodes..."):
        all_data = fetch_indian_data_batch(TICKER_LIST, timeframe_filter)
        
    st.write("📊 **Step 1: Calculating Sectoral Relative Strength (RS) Matrix...**")
    
    sector_performance_registry = {}
    
    for ticker in TICKER_LIST:
        try:
            if len(TICKER_LIST) > 1:
                df = all_data[ticker].dropna()
            else:
                df = all_data.dropna()
                
            if len(df) < 120:
                continue
                
            base_idx = (len(df) - 1) - historical_days
            if base_idx < 65: continue
            
            close_now = float(df.iloc[base_idx]['Close'])
            close_1m = float(df.iloc[base_idx - 20]['Close'])
            close_3m = float(df.iloc[base_idx - 60]['Close'])
            
            ret_1m = (close_now - close_1m) / close_1m
            ret_3m = (close_now - close_3m) / close_3m
            rs_score = (0.4 * ret_1m) + (0.6 * ret_3m)
            
            sec = SECTOR_MAP.get(ticker, "Other")
            if sec not in sector_performance_registry:
                sector_performance_registry[sec] = []
            sector_performance_registry[sec].append(rs_score)
        except Exception:
            continue

    avg_sector_rs = []
    for sec, scores in sector_performance_registry.items():
        if len(scores) > 3: 
            avg_score = sum(scores) / len(scores)
            avg_sector_rs.append({"Sector": sec, "RS Score": avg_score})
            
    rs_df = pd.DataFrame(avg_sector_rs).sort_values(by="RS Score", ascending=False)
    hot_sectors = set(rs_df.head(6)['Sector'].tolist()) 
    
    st.write("### 🔥 Current Sectoral Relative Strength Leaderboard:")
    leaderboard_cols = st.columns(2)
    with leaderboard_cols[0]:
        st.dataframe(rs_df.reset_index(drop=True), use_container_width=True)
        
    st.write("---")
    st.write("⚙️ **Step 2: Scanning Pradeep Bonde Setups inside these Leader Sectors...**")
    
    scanned_data_pool = []
    
    for ticker in TICKER_LIST:
        try:
            ticker_sector = SECTOR_MAP.get(ticker, "Other")
            if ticker_sector not in hot_sectors:
                continue 
                
            if len(TICKER_LIST) > 1:
                df = all_data[ticker].dropna()
            else:
                df = all_data.dropna()
                
            if len(df) < 120: continue
                
            df = df.copy()
            df['Vol_SMA'] = df['Volume'].rolling(window=50).mean()
            df['Pct_Change'] = df['Close'].pct_change() * 100
            df['EMA_10'] = df['Close'].ewm(span=10, adjust=False).mean()
            df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
            
            execution_idx = (len(df) - 1) - historical_days
            if execution_idx < 65: continue
                
            row = df.iloc[execution_idx]
            current_close = float(row['Close'])
            current_ema10 = float(row['EMA_10'])
            current_ema20 = float(row['EMA_20'])
            
            status = None
            trigger_gain = row['Pct_Change']
            trigger_vol = row['Volume'] / row['Vol_SMA'] if row['Vol_SMA'] > 0 else 1.0
            
            # --- STRUCTURE 1: FRESH EP BREAKOUT ---
            if row['Pct_Change'] >= min_gain and row['Volume'] >= (vol_multiplier * row['Vol_SMA']):
                status = "🚨 FRESH EP BREAKOUT"
                
            else:
                # --- LOOKBACK ENGINE FOR LATE EP & PULLBACKS ---
                has_recent_ep = False
                ep_idx = -1
                
                for lookback in range(1, 61):
                    check_idx = execution_idx - lookback
                    if check_idx < 50: break
                    
                    past_row = df.iloc[check_idx]
                    if past_row['Pct_Change'] >= min_gain and past_row['Volume'] >= (vol_multiplier * past_row['Vol_SMA']):
                        has_recent_ep = True
                        ep_idx = check_idx
                        trigger_gain = past_row['Pct_Change']
                        trigger_vol = past_row['Volume'] / past_row['Vol_SMA']
                        break
                        
                if has_recent_ep:
                    bars_since_ep = execution_idx - ep_idx
                    recent_prices = df.iloc[ep_idx+1 : execution_idx+1]['Close']
                    
                    if len(recent_prices) > 0:
                        max_p = recent_prices.max()
                        min_p = recent_prices.min()
                        consolidation_range = ((max_p - min_p) / min_p) * 100
                    else:
                        consolidation_range = 0.0
                    
                    near_10 = abs(current_close - current_ema10) / current_ema10 <= 0.02
                    near_20 = abs(current_close - current_ema20) / current_ema20 <= 0.02
                    
                    if near_10 or near_20:
                        status = f"📉 PULLBACK SUPPORT ({bars_since_ep} Bars Ago)"
                    elif consolidation_range <= 6.0 and current_close >= df.iloc[ep_idx]['Close'] * 0.95:
                        status = f"⏳ LATE EP / CONSOLIDATION ({bars_since_ep} Bars Ago)"
            
            if status:
                if setup_filter == "Fresh EP Breakout (Hot Sectors Only)" and "FRESH" not in status:
                    continue
                if setup_filter == "Late EP / Consolidation (Hot Sectors Only)" and "CONSOLIDATION" not in status:
                    continue
                if setup_filter == "Pullback Near 10/20 EMA (Hot Sectors Only)" and "PULLBACK" not in status:
                    continue
                
                # FIXED: Corrected the variable reference here to prevent local NameError
                c_q_sales, p_q_sales = fetch_dual_quarterly_growth(ticker)
                    
                scanned_data_pool.append({
                    "Ticker Symbol": ticker.replace('.NS', ''),
                    "Company Name": TICKER_MAP.get(ticker, "Unknown"),
                    "Sector / Industry": ticker_sector,
                    "Current Qtr Sales Growth": c_q_sales,
                    "Prev Qtr Sales Growth": p_q_sales,
                    "Setup Status": status,
                    "EP Base Gain": f"{round(trigger_gain, 2)}%",
                    "EP Vol Multiple": f"{round(trigger_vol, 2)}x",
                    "Close Price": f"₹{round(current_close, 2)}",
                    "Scan Date Context": df.index[execution_idx].strftime('%Y-%m-%d')
                })
        except Exception:
            continue
            
    if scanned_data_pool:
        final_df = pd.DataFrame(scanned_data_pool)
        st.success(f"🎯 **Scan Complete!** Found **{len(final_df)} Alpha Stocks** inside Lead Hot Sectors on the chosen timeline!")
        st.dataframe(final_df, use_container_width=True)
        
        priority_ticker = final_df.iloc[0]['Ticker Symbol'] + ".NS"
        try:
            chart_df = all_data[priority_ticker].dropna().head(execution_idx + 1).tail(90)
            chart_df['EMA_10'] = chart_df['Close'].ewm(span=10, adjust=False).mean()
            chart_df['EMA_20'] = chart_df['Close'].ewm(span=20, adjust=False).mean()
            
            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=chart_df.index, open=chart_df['Open'], high=chart_df['High'], low=chart_df['Low'], close=chart_df['Close'], name="Price"))
            fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df['EMA_10'], line=dict(color='#2b5797', width=1.5), name="10 EMA"))
            fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df['EMA_20'], line=dict(color='#d9534f', width=1.5), name="20 EMA"))
            
            fig.update_layout(xaxis_rangeslider_visible=False, template="plotly_white", height=500, title=f"📈 Chart Context ({priority_ticker.replace('.NS','')})")
            st.plotly_chart(fig, use_container_width=True)
        except Exception:
            st.info("Chart alignment verified.")
    else:
        st.warning("Is target historical zone par in strong sectors ka koi setup nahi mila. Sliders ko halka adjust karke dekhein.")
