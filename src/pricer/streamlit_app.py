# --- streamlit_app.py ---
import streamlit as st
from data.data import Data
from plotter.plot import create_volatility_surface, plot_volatility_surface, find_vol_arbitrage
import numpy as np

st.set_page_config(layout="wide", page_title="Volatility Surface Visualizer")

# Initialize Data object
data = Data()

@st.cache_data
def get_data(underlying_symbols: list[str], limit: int = 1000):
    data.contracts_dict = {} # reset the dictionary
    data.get_underlying_details(underlying_symbols)
    data.get_active_options_api(underlying_symbols, limit)
    return data.contracts_dict

st.sidebar.header("Configuration")

user_input = st.sidebar.text_input(
    "Ticker Symbol(s)", 
    value="AAPL", 
    help="Enter a stock ticker (e.g., AAPL). For multiple, separate with commas (e.g., AAPL, TSLA, NVDA)."
)

symbols = [s.strip().upper() for s in user_input.split(",") if s.strip()]
limit_size = st.sidebar.number_input("Contract Limit", min_value=100, max_value=50000, value=1000, step=100)

if not symbols:
    st.warning("Please enter at least one ticker symbol in the sidebar.")
    st.stop()

# Fetch data
with st.spinner(f"Fetching option chains for: {', '.join(symbols)}..."):
    contracts_dict = get_data(symbols, limit_size)

# If no data returned (e.g. invalid ticker)
if not contracts_dict:
    st.error(f"No data found for {symbols}. Please check the ticker symbol.")
    st.stop()

for key, df in contracts_dict.items():
    st.markdown(f"## Option Chain: **{key}**")
    
    # Check if we have enough data
    if df.empty or len(df) < 4:
        st.error("Not enough data points to plot surface.")
        with st.expander(f"View Raw Data ({key})"):
            st.write(df)
        continue

    try:
        # Create grid and plot
        x, y, z = create_volatility_surface(df)

        # Controls Layout
        col1, col2 = st.columns([1, 2])

        # Toggle
        with col1:
            show_anomalies = st.toggle("Show Volatility Anomalies", value=False, key=key)

        anomaly_mask = None # Default to None so the plot ignores it

        # Only show the slider and calculate if toggle is ON
        if show_anomalies:
            with col2:
                threshold = st.slider( # Interactive Threshold Slider
                    "Gradient Threshold (Sensitivity)", 
                    min_value=0.01, 
                    max_value=1.0, 
                    value=0.1, 
                    step=0.01,
                    help="Lower values detect smaller changes in volatility. Higher values only detect extreme jumps."
                )
                # Find Anomalies
                anomaly_mask = find_vol_arbitrage(z, threshold=threshold)
                num_anomalies = np.sum(anomaly_mask)
                st.metric("Anomalies Detected", int(num_anomalies))

        fig = plot_volatility_surface(x, y, z, anomaly_mask)

        # Render with Streamlit
        st.plotly_chart(fig, width="stretch")

        with st.expander("View Raw Data"):
            st.write(df[["expiration_date", "strike_price", "close_price", "calculated_iv"]])
            
    except Exception as e:
        st.error(f"Error plotting surface: {e}")
        st.write("Ensure your calculated_iv column has valid non-NaN values.")