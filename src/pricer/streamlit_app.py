import streamlit as st
from data.data import Data
from plotter.plot import create_volatility_surface, plot_volatility_surface

data = Data()

@st.cache_data
def get_data(underlying_symbols: list[str], limit: int = 1000):
  data.get_active_options_api(underlying_symbols, limit)
  return data.contract_df

df = get_data(["AAPL"], 1000)
st.title(f"Option Chain: {df.iloc[0]["underlying_symbol"]}")

x,y,z = create_volatility_surface(df)
plt = plot_volatility_surface(x,y,z)

st.pyplot(plt)

st.write(df)
