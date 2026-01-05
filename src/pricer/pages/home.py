import streamlit as st

st.set_page_config(
    page_title="Quant Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("Quant Option Analytics Dashboard")

st.markdown("""
### Welcome to the Option Analytics Suite

This application is designed to visualize market data and price exotic options using Monte Carlo simulations. 

Please navigate using the sidebar to access the following tools:

#### 1. 📈 Volatility Surface Visualizer
*   **Purpose**: Analyze the Implied Volatility (IV) surface of options across different strikes and expirations.
*   **Features**: 
    *   3D Interactive Surface Plots.
    *   Arbitrage/Anomaly detection (Gradient Thresholding).
    *   Saves market data to session state for pricing.

#### 2. 🎲 Asian Option Pricer
*   **Purpose**: Price Asian Options (Arithmetic Average) using Monte Carlo simulations.
*   **Features**:
    *   Visualize random walk paths.
    *   Import market data directly from the Volatility Surface tool.
    *   Calculate Fair Value.

---
*Select a page from the sidebar to begin.*
""")