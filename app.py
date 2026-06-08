import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Page Configuration
st.set_page_config(page_title="Ultra-Fast NSE Catalyst Scanner", layout="wide")
st.title("⚡ Ultra-Fast Stock Scanner: Circuit Breakout & Consolidation (Full NSE)")
st.write("Scans the entire 2000+ NSE market in seconds using high-speed Multi-Threading Bulk Download.")

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
def load_live_nse_universe():
    try:
        url = "https://raw.githubusercontent.com/anirbanb/nse-ticker-list/master/nse_tickers.csv"
        backup_url = "https://raw.githubusercontent.com/shangb/NSE-equity-list/master/equity.csv"
        try:
            df = pd.read_csv(url)
            symbol_col = [c for c in df.columns if 'SYMBOL' in c.upper() or 'TICKER' in c.upper()][0]
            raw_symbols = df[symbol_col].dropna().tolist()
        except Exception:
            df = pd.read_csv(backup_nse_url)
            raw_symbols = df['SYMBOL'].dropna().tolist()
            
        validated_tickers = [f"{str(sym).strip().upper()}.NS" for sym in raw_symbols if str(sym).strip().isalnum() and not str(sym).isdigit()]
        return sorted(list(set(validated_tickers)))
    except Exception:
        return ["HGINFRA.NS", "PARAS.NS", "CGPOWER.NS", "RTNINDIA.NS", "COCHINSHIP.NS", "GRSE.NS", "RAILTEL.NS", "BEL.NS"]

with st.spinner("Fetching Live NSE Ticker Database..."):
    tickers = load_live_nse_universe()
st.sidebar.success(f"🎯 Total Active Stocks Loaded: {len(tickers)}")

# --- LIVE NEWS FETCH VIA YFINANCE OBJECTS SAFELY ---
def get_quick_news(ticker_obj):
    try:
        news = ticker_obj.news
        if news and len(news) > 0:
            return news[0]['title']
    except Exception:
        pass
    return "N.A."

# --- BULLETPROOF ENGINE ---
def run_fast_scan(ticker_list, min_move, vol_mult, cons_days, lookback, max_cons):
    scanned_data = []
    
    end_date = datetime.today()
    start_date = end_date - timedelta(days=lookback + 45)
    
    # STEP 1: BULK DOWNLOAD (The Game Changer)
    # Yeh saare 2500 stocks ka data ek sath background me parallelly parallel threads par pull karega
    with st.spinner(f"📥 Downloading historical data for all {len(ticker_list)} stocks simultaneously via Multi-Threading..."):
        bulk_data = yf.download(
            tickers=ticker_list, 
            start=start_date.strftime('%Y-%m-%d'), 
            end=end_date.strftime('%Y-%m-%d'), 
            group_by='ticker', 
            threads=True, # High speed processing active
            progress=False
        )
    
    # STEP 2: FAST LOCAL MEMORY PROCESSING
    status_text = st.empty()
    progress_bar = st.progress(0)
    
    # Filter out active tickers that actually returned data
    available_tickers = list(set([t for t in bulk_data.columns.get_level_values(0)]))
    total_to_process = len(available_tickers)
    
    for idx, ticker in enumerate(available_tickers):
        progress_bar.progress((idx + 1) / total_to_process)
        if idx % 50 == 0:
            status_text.text(f"Processing & Filtering: {idx}/{total_to_process} stocks analysed...")
            
        try:
            # Extract stock specific dataframe from memory
            df = bulk_data[ticker].dropna(subset=['Close'])
            
            if len(df) < 25:
                continue
                
            df['Daily_Return'] = df['Close'].pct_change() * 100
            df['Avg_Vol_20'] = df['Volume'].rolling(window=20).mean()
            
            # Slice strictly to the lookback window
            search_df = df.tail(lookback)
            circuit_days = search_df[search_df['Daily_Return'] >= min_move]
            
            if not circuit_days.empty:
                last_circuit_row = circuit_days.iloc[-1]
                circuit_date = circuit_days.index[-1]
                
                if pd.isna(last_circuit_row['Avg_Vol_20']) or last_circuit_row['Avg_Vol_20'] == 0:
                    continue
                    
                # Volume Condition
                if last_circuit_row['Volume'] >= (last_circuit_row['Avg_Vol_20'] * vol_mult):
                    
                    # Consolidation Check
                    recent_df = df.tail(cons_days)
                    if len(recent_df) >= cons_days:
                        max_close = recent_df['Close'].max()
                        min_close = recent_df['Close'].min()
                        
                        consolidation_range = ((max_close - min_close) / min_close) * 100
                        
                        if consolidation_range <= max_cons:
                            # Fetch news dynamically via standard object call safely
                            stk_obj = yf.Ticker(ticker)
                            news_headline = get_quick_news(stk_obj)
                            
                            breakout_volume_mn = last_circuit_row['Volume'] / 1_000_000
                                
                            scanned_data.append({
                                "Stock Ticker": ticker,
                                "Current Price": round(df['Close'].iloc[-1], 2),
                                f"{min_move}%+ Breakout Date": circuit_date.strftime('%Y-%m-%d'),
                                "Move % on Breakout Day": round(last_circuit_row['Daily_Return'], 2),
                                "Breakout Day Volume (Mn)": f"{round(breakout_volume_mn, 2)} M",
                                "Recent Consolidation Range": f"{round(consolidation_range, 2)}%",
                                "Catalyst News / Latest Trigger": news_headline
                            })
                            
        except Exception:
            continue
            
    status_text.text("Scan completed successfully across all equities!")
    return pd.DataFrame(scanned_data)

# --- RUN SCANNER ---
if st.button("🚀 Run 2500+ Complete Market Scan"):
    results_df = run_fast_scan(tickers, min_move, volume_multiplier, consolidation_days, lookback_days, max_consolidation_allowed)
    
    if not results_df.empty:
        st.success(f"🎯 Match Found! Identified {len(results_df)} stocks matching your exact framework!")
        st.dataframe(
            results_df, 
            use_container_width=True,
            column_config={
                "Catalyst News / Latest Trigger": st.column_config.TextColumn(width="large")
            }
        )
        
        csv = results_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export Complete List to CSV", csv, "live_nse_scan_output.csv", "text/csv")
    else:
        st.error("No stocks matched the exact parameters. Try widening the consolidation bands or lower the breakout move range.")
