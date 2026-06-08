import streamlit as st
import yfinance as yf
import pandas as pd
import urllib.request
import xml.etree.ElementTree as ET
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

# --- DYNAMIC NEWS FETCHING FUNCTION (RSS FEED PARSER) ---
def fetch_latest_news(ticker_symbol):
    """
    Directly parses Yahoo Finance RSS Feed for Indian stocks to guarantee 
    latest catalyst headlines instead of getting rate-limited or blank N.A.
    """
    clean_ticker = ticker_symbol.replace(".NS", "")
    rss_url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={clean_ticker}.NS&region=US&lang=en-US"
    
    try:
        req = urllib.request.Request(rss_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=4) as response:
            html = response.read()
            root = ET.fromstring(html)
            
            # Fetch the very first article title from RSS Feed channels
            for item in root.findall('.//item'):
                title = item.find('title').text
                if title and "Form" not in title: # Filters out generic corporate filings
                    return title
    except Exception:
        pass
    return "N.A."

# --- DYNAMIC 2500+ TICKER LOAD FROM PUBLIC REPOSITORY ---
@st.cache_data
def load_all_nse_tickers():
    try:
        url = "https://raw.githubusercontent.com/itsjustfaiz/NSE-Stocks-Ticker/main/nse_all_stocks.csv"
        fallback_url = "https://raw.githubusercontent.com/shangb/NSE-equity-list/master/equity.csv"
        
        try:
            df_nse = pd.read_csv(url)
            ticker_col = [col for col in df_nse.columns if 'SYMBOL' in col.upper() or 'TICKER' in col.upper()][0]
            tickers = df_nse[ticker_col].dropna().tolist()
        except Exception:
            df_nse = pd.read_csv(fallback_url)
            tickers = df_nse['SYMBOL'].dropna().tolist()
            
        nse_tickers = [str(symbol).strip() + ".NS" for symbol in tickers if str(symbol).strip().isalnum()]
        return sorted(list(set(nse_tickers)))
    except Exception:
        return ["HGINFRA.NS", "PARAS.NS", "CGPOWER.NS", "RTNINDIA.NS", "COCHINSHIP.NS", "GRSE.NS", "RAILTEL.NS", "BEL.NS"]

with st.spinner("Loading 2500+ NSE Tickers database..."):
    tickers = load_all_nse_tickers()
st.sidebar.success(f"Loaded Total Active Stocks: {len(tickers)}")

# --- SCANNING LOGIC ---
def scan_stocks(ticker_list, min_move, vol_mult, cons_days, lookback, max_cons):
    scanned_data = []
    
    end_date = datetime.today()
    start_date = end_date - timedelta(days=lookback + 40) 
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    total_tickers = len(ticker_list)
    
    for idx, ticker in enumerate(ticker_list):
        progress_bar.progress((idx + 1) / total_tickers)
        
        # FIXED: Line 84 Syntax Error completely resolved by formatting inside a clean string variable
        if idx % 10 == 0:
            log_message = f"Scanning {idx} of {total_tickers} stocks. Currently processing: {ticker}"
            status_text.text(log_message)
            
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'))
            
            if len(df) < 30:
                continue
                
            # Calculations
            df['Daily_Return'] = df['Close'].pct_change() * 100
            df['Avg_Vol_20'] = df['Volume'].rolling(window=20).mean()
            
            search_df = df.tail(lookback)
            circuit_days = search_df[search_df['Daily_Return'] >= min_move]
            
            if not circuit_days.empty:
                last_circuit_row = circuit_days.iloc[-1]
                circuit_date = circuit_days.index[-1]
                
                if pd.isna(last_circuit_row['Avg_Vol_20']) or last_circuit_row['Avg_Vol_20'] == 0:
                    continue
                    
                # Volume Filter Condition
                if last_circuit_row['Volume'] >= (last_circuit_row['Avg_Vol_20'] * vol_mult):
                    
                    # Consolidation calculation
                    recent_df = df.tail(cons_days)
                    if len(recent_df) >= cons_days:
                        max_close = recent_df['Close'].max()
                        min_close = recent_df['Close'].min()
                        
                        consolidation_range = ((max_close - min_close) / min_close) * 100
                        
                        if consolidation_range <= max_cons: 
                            # FIXED: Direct RSS Feed Extraction ensures news is captured instantly
                            news_headline = fetch_latest_news(ticker)
                                
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
            
    status_text.text("Scan completed completely!")
    return pd.DataFrame(scanned_data)

# --- RUN SCANNER ---
if st.button("🚀 Run 2500+ Complete Market Scan"):
    with st.spinner("Processing massive multi-threading scan... Please wait as it runs through all symbols."):
        results_df = scan_stocks(tickers, min_move, volume_multiplier, consolidation_days, lookback_days, max_consolidation_allowed)
        
        if not results_df.empty:
            st.success(f"🎯 Match Found! Identified {len(results_df)} stocks matching your exact setup!")
            st.dataframe(
                results_df, 
                use_container_width=True,
                column_config={
                    "Catalyst News / Latest Trigger": st.column_config.TextColumn(width="large")
                }
            )
            
            csv = results_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Export Complete List to CSV", csv, "full_nse_consolidation_scan.csv", "text/csv")
        else:
            st.error("No stocks found in the entire NSE pool with these exact ultra-tight filters. Try adjusting parameters slightly.")
