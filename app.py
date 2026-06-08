import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Page Configuration
st.set_page_config(page_title="Advanced Catalyst & Consolidation Scanner", layout="wide")
st.title("📊 Advanced Stock Scanner: Circuit Breakout & Consolidation")
st.write("Scan market for historical sharp moves, volume expansion, and recent tight consolidation.")

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
    min_value=3, max_value=15, value=5, step=1
)

max_consolidation_allowed = st.sidebar.slider(
    "Max Allowed Consolidation Band (%)",
    min_value=5.0, max_value=20.0, value=12.0, step=0.5
)

# Broad Ticker Pool (NSE Stocks)
@st.cache_data
def load_tickers():
    return [
        "HGINFRA.NS", "PARAS.NS", "CGPOWER.NS", "RTNINDIA.NS", "COCHINSHIP.NS", 
        "GRSE.NS", "RAILTEL.NS", "DIVISLAB.NS", "HINDALCO.NS", "NATIONALUM.NS", 
        "BEL.NS", "RAMCOSYS.NS", "RITES.NS", "NRBBEARING.NS", "GODIGIT.NS",
        "TATASTEEL.NS", "RELIANCE.NS", "IRFC.NS", "RVNL.NS", "BHEL.NS",
        "AWFIS.NS", "EXICOM.NS", "MAHSEAMLES.NS", "INFY.NS", "TATAMOTORS.NS"
    ]

tickers = load_tickers()

# --- SCANNING LOGIC ---
def scan_stocks(ticker_list, min_move, vol_mult, cons_days, lookback, max_cons):
    scanned_data = []
    
    end_date = datetime.today()
    # Adding a massive 40 days buffer to ensure 20-day moving averages never return NaN
    start_date = end_date - timedelta(days=lookback + 40) 
    
    progress_bar = st.progress(0)
    total_tickers = len(ticker_list)
    
    for idx, ticker in enumerate(ticker_list):
        progress_bar.progress((idx + 1) / total_tickers)
        
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'))
            
            if len(df) < 30:
                continue
                
            # Calculations
            df['Daily_Return'] = df['Close'].pct_change() * 100
            df['Avg_Vol_20'] = df['Volume'].rolling(window=20).mean()
            
            # Extract data specifically for the lookback period to find the circuit day
            search_df = df.tail(lookback)
            circuit_days = search_df[search_df['Daily_Return'] >= min_move]
            
            if not circuit_days.empty:
                last_circuit_row = circuit_days.iloc[-1]
                circuit_date = circuit_days.index[-1]
                
                # Check if volume data is valid
                if pd.isna(last_circuit_row['Avg_Vol_20']) or last_circuit_row['Avg_Vol_20'] == 0:
                    continue
                    
                # Volume Condition
                if last_circuit_row['Volume'] >= (last_circuit_row['Avg_Vol_20'] * vol_mult):
                    
                    # Consolidation Check: Focus strictly on the very recent days closing prices
                    recent_df = df.tail(cons_days)
                    if len(recent_df) >= cons_days:
                        max_close = recent_df['Close'].max()
                        min_close = recent_df['Close'].min()
                        
                        # Calculating close-to-close tight range matrix
                        consolidation_range = ((max_close - min_close) / min_close) * 100
                        
                        if consolidation_range <= max_cons: 
                            # Fetch News Safety Block
                            news_headline = "N.A."
                            try:
                                news_list = stock.news
                                if news_list and len(news_list) > 0:
                                    news_headline = news_list[0]['title']
                            except Exception:
                                news_headline = "N.A."
                                
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
                            
        except Exception as e:
            st.sidebar.write(f"Log Error ({ticker}): {str(e)}")
            continue
            
    return pd.DataFrame(scanned_data)

# --- RUN SCANNER ---
if st.button("🚀 Run Market Scan"):
    with st.spinner("Processing historical delivery data and matching consolidation setups..."):
        results_df = scan_stocks(tickers, min_move, volume_multiplier, consolidation_days, lookback_days, max_consolidation_allowed)
        
        if not results_df.empty:
            st.success(f"Found {len(results_df)} stocks matching your exact framework!")
            st.dataframe(
                results_df, 
                use_container_width=True,
                column_config={
                    "Catalyst News / Latest Trigger": st.column_config.TextColumn(width="large")
                }
            )
            
            csv = results_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Export List to CSV", csv, "active_consolidation_scan.csv", "text/csv")
        else:
            st.error("No stocks found! Best Setting for Results: Keep Consolidation Period at 5 days & Max Allowed Consolidation Band at 12%.")
