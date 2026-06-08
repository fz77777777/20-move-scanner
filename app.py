import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Page Configuration
st.set_page_config(page_title="Advanced Catalyst & Consolidation Scanner", layout="wide")
st.title("📊 Advanced Stock Scanner: Circuit Breakout & Consolidation")
st.write("Scan 2500+ stocks for historical sharp moves, volume expansion, and recent tight consolidation.")

# --- SIDEBAR FILTERS ---
st.sidebar.header("🔍 Filter Parameters")

# 1. Percentage Move Filter
min_move = st.sidebar.slider(
    "Select Minimum Circuit/Sharp Move (%)", 
    min_value=10, max_value=20, value=20, step=1
)

# 2. Volume Filter
volume_multiplier = st.sidebar.slider(
    "Volume Spurt Filter (X times of 20-day Avg Volume on breakout day)", 
    min_value=1.5, max_value=10.0, value=3.0, step=0.5
)

# 3. Consolidation Days
consolidation_days = st.sidebar.number_input(
    "Consolidation Period (Recent Days)", 
    min_value=3, max_value=20, value=7
)

# Dummy Ticker List for Demo (You can replace this with 2500+ NSE/BSE tickers from a CSV)
@st.cache_data
def load_tickers():
    return [
        "HGINFRA.NS", "PARAS.NS", "CGPOWER.NS", "RTNINDIA.NS", "COCHINSHIP.NS", 
        "GRSE.NS", "RAILTEL.NS", "DIVISLAB.NS", "HINDALCO.NS", "NATIONALUM.NS", 
        "BEL.NS", "RAMCOSYS.NS", "RITES.NS", "NRBBEARING.NS", "GODIGIT.NS"
    ]

tickers = load_tickers()

# --- SCANNING LOGIC ---
def scan_stocks(ticker_list, min_move, vol_mult, cons_days):
    scanned_data = []
    
    # 2 months historical data timeframe
    end_date = datetime.today()
    start_date = end_date - timedelta(days=60)
    
    progress_bar = st.progress(0)
    total_tickers = len(ticker_list)
    
    for idx, ticker in enumerate(ticker_list):
        progress_bar.progress((idx + 1) / total_tickers)
        
        try:
            # Fetch data
            stock = yf.Ticker(ticker)
            df = stock.history(start=start_date, end=end_date)
            
            if len(df) < 20:
                continue
                
            # Calculate daily returns and 20-day Average Volume
            df['Daily_Return'] = df['Close'].pct_change() * 100
            df['Avg_Vol_20'] = df['Volume'].rolling(window=20).mean()
            
            # Find the day when stock hit the required % move (Circuit Day)
            circuit_days = df[df['Daily_Return'] >= min_move]
            
            if not circuit_days.empty:
                # Get the most recent circuit day within 2 months
                last_circuit_row = circuit_days.iloc[-1]
                circuit_date = circuit_days.index[-1]
                
                # Check Volume Condition on Circuit Day
                if last_circuit_row['Volume'] >= (last_circuit_row['Avg_Vol_20'] * vol_mult):
                    
                    # Check Consolidation Condition (Recent 'cons_days' price action should be tight)
                    recent_df = df.tail(cons_days)
                    if len(recent_df) >= cons_days:
                        max_price = recent_df['High'].max()
                        min_price = recent_df['Low'].min()
                        
                        # Tight consolidation check (Range should be within 6.5% volatility)
                        consolidation_range = ((max_price - min_price) / min_price) * 100
                        
                        if consolidation_range <= 6.5: 
                            # Fetch Catalyst News if available
                            news_headline = "N.A."
                            try:
                                news_list = stock.news
                                if news_list:
                                    news_headline = news_list[0]['title']
                            except Exception:
                                news_headline = "N.A."
                                
                            # Calculate volume in millions for clean display
                            breakout_volume_mn = last_circuit_row['Volume'] / 1_000_000
                                
                            scanned_data.append({
                                "Stock Ticker": ticker,
                                "Current Price": round(df['Close'].iloc[-1], 2),
                                f"{min_move}% Circuit Date": circuit_date.strftime('%Y-%m-%d'),
                                "Move % on that Day": round(last_circuit_row['Daily_Return'], 2),
                                "Breakout Day Volume (Mn)": f"{round(breakout_volume_mn, 2)} M",
                                "Consolidation Range (%)": f"{round(consolidation_range, 2)}%",
                                "Catalyst News / Latest Trigger": news_headline
                            })
                            
        except Exception as e:
            continue
            
    return pd.DataFrame(scanned_data)

# --- RUN SCANNER ---
if st.button("🚀 Run 2500+ Market Scan"):
    with st.spinner("Scanning historical charts for patterns, volumes, and news triggers..."):
        results_df = scan_stocks(tickers, min_move, volume_multiplier, consolidation_days)
        
        if not results_df.empty:
            st.success(f"Found {len(results_df)} stocks matching your criteria!")
            
            # Display interactive Dataframe
            st.dataframe(
                results_df, 
                use_container_width=True,
                column_config={
                    "Breakout Day Volume (Mn)": st.column_config.TextColumn("Breakout Vol (Mn)", help="Volume traded on the day of sharp upmove."),
                    "Catalyst News / Latest Trigger": st.column_config.TextColumn(width="large")
                }
            )
            
            # Download Button for Excel/CSV export
            csv = results_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Export List to CSV", csv, "circuit_consolidation_scan.csv", "text/csv")
        else:
            st.warning("No stocks found with the current filter criteria. Try tweaking the filters.")
