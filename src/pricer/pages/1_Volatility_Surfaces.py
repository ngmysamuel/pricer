import numpy as np
import streamlit as st
from data.data import Data

from pricer.plotter.plot_volatility_surface import (
    create_volatility_surface,
    find_vol_arbitrage,
    plot_volatility_surface,
)

# Configure page
st.set_page_config(layout="wide", page_title="Volatility Surface", page_icon="📈")

st.title("Volatility Surface Visualizer")
st.markdown("Analyze implied volatility surfaces to detect market anomalies.")

# --- Sidebar: Configuration Specific to this Page ---
st.sidebar.header("Data Configuration")
user_input = st.sidebar.text_input(
    "Ticker Symbol(s)", 
    value="AAPL", 
    help="Enter ticker (e.g., AAPL). Separate multiples with commas."
)
limit_size = st.sidebar.number_input("Contract Limit", min_value=100, max_value=50000, value=1000, step=100, help="Max number of options to pull per ticker")

# Process Symbols
symbols = [s.strip().upper() for s in user_input.split(",") if s.strip()]

# Initialize Data
data = Data()

@st.cache_data
def get_data(underlying_symbols: list[str], limit: int = 1000):
    data.contracts_dict = {} 
    data.get_underlying_details(underlying_symbols)
    data.get_active_options_api(underlying_symbols, limit)
    return data.contracts_dict

if not symbols:
    st.warning("Please enter a ticker symbol in the sidebar.")
    st.stop()

# Fetch Data
with st.spinner(f"Fetching option chains for: {', '.join(symbols)}..."):
    contracts_dict = get_data(symbols, limit_size)

if not contracts_dict:
    st.error(f"No data found for {symbols}.")
    st.stop()

# Adjustable resliution for interpolation based on the number of valid data points
max_resolution = min([val.shape[0] for val in contracts_dict.values()])
resolution = st.sidebar.number_input("Surface Resolution", min_value=50, max_value=max_resolution, value=50, step=10, help=f"Higher = smoother but slower. Max = {max_resolution}")

page_2_data = {}

# --- Main Visualization Loop ---
for key, df in contracts_dict.items():
    st.markdown(f"### Option Chain: **{key}**")
    
    if df.empty or len(df) < 4:
        st.error("Not enough data points to plot surface.")
        continue

    # --- Save Data for Monte Carlo Page ---
    # We grab the latest close price and a median IV to help seed the next page
    latest_price = data.asset_price_dict[key] if key in data.asset_price_dict else 100.0
    avg_iv = df['calculated_iv'].median() if 'calculated_iv' in df.columns else 0.2
    
    # Save to Session State so Page 2 can see it
    page_2_data[key] = {
        'symbol': key,
        'price': latest_price,
        'vol': avg_iv
    }
    # ---------------------------------------------

    try:
        x, y, z = create_volatility_surface(df, resolution)
        
        # Local Controls
        col1, col2 = st.columns([1, 2])
        with col1:
            show_anomalies = st.toggle("Show Anomalies", value=False, key=f"tog_{key}")

        anomaly_mask = None 
        if show_anomalies:
            with col2:
                threshold = st.slider("Gradient Threshold", 0.01, 1.0, 0.1, 0.01, key=f"thresh_{key}")
                anomaly_mask = find_vol_arbitrage(z, threshold=threshold)
                st.metric("Anomalies Detected", int(np.sum(anomaly_mask)))

        fig = plot_volatility_surface(x, y, z, anomaly_mask)
        st.plotly_chart(fig, width="stretch")
        
        st.info(f"💡 **Analysis for {key}:** Data saved. Navigate to 'Asian Option Pricer' in the sidebar to price options using this data.")
            
    except Exception as e:
        st.error(f"Error plotting surface: {e}")

st.session_state["page_2_data"] = page_2_data