import numpy as np
import streamlit as st

from pricer.model.monte_carlo import MonteCarlo
from pricer.plotter.plot_monte_carlo import plot_traces
from pricer.plotter.plot_volatility_surface import plot_volatility_surface

st.set_page_config(layout="wide", page_title="Asian Option Pricer", page_icon="🎲")
st.title("Monte Carlo: Asian Option Pricer")

# Get data from previous page
available_data = st.session_state.get('page_2_data', {})

# Create list for dropdown
ticker_options = ["Manual Entry"] + list(available_data.keys())

# --- Layout ---
col_params, col_plot = st.columns([1, 3])

with col_params:
    st.subheader("Configuration")
    
    # 1. Ticker Selection
    selected_ticker = st.selectbox(
        "Select Underlying Asset", 
        options=ticker_options,
        help="Select a ticker analyzed in the Volatility Surface page, or use Manual Entry."
    )

    # 2. Determine Default Values based on selection
    if selected_ticker != "Manual Entry":
        data = available_data[selected_ticker]
        default_price = float(data['price'])
        # Ensure vol is valid
        default_vol = float(data['vol']) if data['vol'] > 0 else 0.2
        st.success(f"Loaded data for **{selected_ticker}**")
    else:
        default_price = 100.0
        default_vol = 0.2

    st.markdown("---")
    
    # 3. Input Fields (Pre-filled)
    mc_price = st.number_input("Current Asset Price ($)", value=default_price, step=0.5)

    mc_type = st.selectbox("Option Type", ["call", "put"])
    
    # Default strike to 5% OTM roughly
    default_strike = round(mc_price * 1.05, 2) if mc_type == "call" else round(mc_price * 0.95, 2)
    mc_strike = st.number_input("Strike Price ($)", value=default_strike, step=0.5, help="Defaulted to the 5% OTM")
    
    if selected_ticker != "Manual Entry":
        mc_vol = st.number_input("Volatility (σ)", value=0, disabled=True)
        st.info("Utilizing local volatility from implied volatility from previous page")
    else:
        mc_vol = st.number_input("Volatility (σ)", value=default_vol, step=0.01, format="%.4f", help="Defaulted to median of IVs calculated in the previous page")
    
    mc_r = st.number_input("Risk Free Rate (r)", value=0.035, step=0.001, format="%.3f")
    mc_days = st.number_input("Days to Expiration", value=30, step=1)
    mc_iter = st.number_input("Iterations", value=1000, step=100, max_value=1000000)
    
    st.markdown("---")
    run_sim = st.button("Run Simulation", type="primary", use_container_width=True)

with col_plot:
    if run_sim:
        mc = MonteCarlo(maturities=data["maturities"],strike_prices=data["strike_prices"],implied_vol=data["implied_vol"],asset_price=data["price"],q=data["dividend_yield"],r=mc_r)
        with st.spinner("Spinning up local volatility surface from implied volatility"):
            mc.local_volatility()
        with st.spinner(f"Simulating {mc_iter} paths for {selected_ticker}..."):
            calc_price, paths = mc.simple_random_walk(
                current_price=mc_price,
                volatility=mc_vol,
                strike=mc_strike,
                typ=mc_type,
                path_length=int(mc_days),
                iterations=int(mc_iter)
            )

        # --- Results ---
        # Layout metrics
        m1, m2, m3 = st.columns(3)
        m1.metric(f"Fair Value ({mc_type.title()})", f"${calc_price:.4f}")
        
        final_prices = paths[:, -1]
        itm_prob = np.mean(final_prices > mc_strike) if mc_type == "call" else np.mean(final_prices < mc_strike)
        m2.metric("ITM Probability", f"{itm_prob:.1%}")
        
        avg_final = np.mean(final_prices)
        m3.metric("Avg. Final Price", f"${avg_final:.2f}")

        # --- Plotting ---
        fig_mc = plot_traces(paths, mc_price, mc_strike, mc_iter, selected_ticker)
        st.plotly_chart(fig_mc, width='stretch')

        
        lv_surface_plot = plot_volatility_surface(data["maturities"], data["strike_prices"], mc.lv_raw, 'Local Volatility')
        st.plotly_chart(lv_surface_plot, width="stretch")