import streamlit as st
from data.data import Data
from plotter.plot import create_volatility_surface, plot_volatility_surface

data = Data()


@st.cache_data
def get_data(underlying_symbols: list[str], limit: int = 1000):
    data.get_underlying_details(underlying_symbols)
    data.get_active_options_api(underlying_symbols, limit)
    # data.get_active_options_csv(underlying_symbols)
    return data.contracts_dict


contracts_dict = get_data(["AAPL"], 1000)

for key, df in contracts_dict.items():
    st.title(f"Option Chain: {key}")

    x, y, z = create_volatility_surface(df)
    plt = plot_volatility_surface(x, y, z)

    st.pyplot(plt)

    st.write(df)
