# --- streamlit_app.py ---
import streamlit as st
from data.data import Data
from plotter.plot import create_volatility_surface, plot_volatility_surface

# Initialize Data object
data = Data()

@st.cache_data
def get_data(underlying_symbols: list[str], limit: int = 1000):
    data.get_underlying_details(underlying_symbols)
    data.get_active_options_api(underlying_symbols, limit)
    return data.contracts_dict

# Fetch data
contracts_dict = get_data(["AAPL"], 1000)

for key, df in contracts_dict.items():
    st.title(f"Option Chain: {key}")
    
    # Check if we have enough data
    if df.empty or len(df) < 4:
        st.error("Not enough data points to plot surface.")
        st.write(df)
        continue

    try:
        # Create grid and plot
        x, y, z = create_volatility_surface(df)
        fig = plot_volatility_surface(x, y, z)

        # Render with Streamlit
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("View Raw Data"):
            st.write(df[["expiration_date", "strike_price", "close_price", "calculated_iv"]])
            
    except Exception as e:
        st.error(f"Error plotting surface: {e}")
        st.write("Ensure your calculated_iv column has valid non-NaN values.")