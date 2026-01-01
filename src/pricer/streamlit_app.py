# --- streamlit_app.py ---
import streamlit as st
from data.data import Data
from plotter.plot import create_volatility_surface, plot_volatility_surface, find_vol_arbitrage
import numpy as np
from pricer.model.monte_carlo import MonteCarlo
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Volatility Surface & Pricer")

# Initialize Data object
data = Data()

@st.cache_data
def get_data(underlying_symbols: list[str], limit: int = 1000):
    data.contracts_dict = {} # reset the dictionary
    data.get_underlying_details(underlying_symbols)
    data.get_active_options_api(underlying_symbols, limit)
    return data.contracts_dict

# Config for all tabs
st.sidebar.header("Global Configuration")
user_input = st.sidebar.text_input(
    "Ticker Symbol(s)", 
    value="AAPL", 
    help="Enter a stock ticker (e.g., AAPL). For multiple, separate with commas (e.g., AAPL, TSLA, NVDA)."
)
symbols = [s.strip().upper() for s in user_input.split(",") if s.strip()]
limit_size = st.sidebar.number_input("Contract Limit", min_value=100, max_value=50000, value=1000, step=100)

# Set up tabs
tab_surface, tab_mc = st.tabs(["Volatility Surface", "Monte Carlo Pricer"])

# ==========================================
# TAB 1: VOLATILITY SURFACE
# ==========================================
with tab_surface:
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

# ==========================================
# TAB 2: MONTE CARLO SIMULATION
# ==========================================
with tab_mc:
    st.markdown("### Monte Carlo Option Pricing (Asian Option)")
    st.write("Simulate random walks to price an Asian option based on the parameters below.")
    
    col_params, col_plot = st.columns([1, 3])

    with col_params:
        st.subheader("Parameters")
        # Inputs
        mc_price = st.number_input("Current Asset Price ($)", value=100.0)
        mc_strike = st.number_input("Strike Price ($)", value=110.0)
        mc_vol = st.number_input("Volatility (sigma)", value=0.2, step=0.01)
        mc_r = st.number_input("Risk Free Rate (r)", value=0.035, step=0.001)
        mc_days = st.number_input("Days to Expiration", value=30, step=1)
        mc_iter = st.number_input("Iterations", value=500, step=100, max_value=5000)
        mc_type = st.selectbox("Option Type", ["call", "put"])
        
        run_sim = st.button("Run Simulation", type="primary")

    with col_plot:
        if run_sim:
            with st.spinner("Simulating Random Walks..."):
                mc = MonteCarlo()
                calc_price, paths = mc.simple_random_walk(
                    current_price=mc_price,
                    volatility=mc_vol,
                    strike=mc_strike,
                    typ=mc_type,
                    path_length=int(mc_days),
                    iterations=int(mc_iter),
                    r=mc_r
                )

            # --- Metrics ---
            st.metric(
                label=f"Calculated Fair Value", 
                value=f"${calc_price:.4f}",
                delta=None
            )

            # --- Plotting Paths ---
            fig_mc = go.Figure()
            
            # X-axis represents days (0 to path_length)
            days_axis = list(range(paths.shape[1]))

            # Plot a subset of paths to prevent browser lag if iterations > 500
            display_limit = min(int(mc_iter), 200)
            
            # Add individual paths
            for i in range(display_limit):
                fig_mc.add_trace(go.Scatter(
                    x=days_axis,
                    y=np.concatenate((np.array([mc_price]), paths[i])),
                    mode='lines',
                    line=dict(width=1, color='rgba(0, 150, 255, 0.15)'), # Transparent Blue
                    showlegend=False,
                    hoverinfo='skip'
                ))

            # Add Strike Price Line
            fig_mc.add_hline(
                y=mc_strike, 
                line_dash="dash", 
                line_color="red", 
                annotation_text=f"Strike ${mc_strike}"
            )

            # Add Average Path Line
            avg_path = np.mean(paths, axis=0)
            fig_mc.add_trace(go.Scatter(
                x=days_axis,
                y=avg_path,
                mode='lines',
                line=dict(width=3, color='orange'),
                name='Average Path'
            ))

            fig_mc.update_layout(
                title=f"Monte Carlo Paths ({mc_iter} iterations)",
                xaxis_title="Days",
                yaxis_title="Asset Price",
                template="plotly_dark",
                height=550,
                hovermode="x"
            )

            st.plotly_chart(fig_mc, width='stretch')
            
            # Stats
            with st.expander("Show Simulation Statistics"):
                final_prices = paths[:, -1]
                stats_col1, stats_col2, stats_col3 = st.columns(3)
                stats_col1.metric("Min Final Price", f"${np.min(final_prices):.2f}")
                stats_col2.metric("Max Final Price", f"${np.max(final_prices):.2f}")
                stats_col3.metric("Mean Final Price", f"${np.mean(final_prices):.2f}")
