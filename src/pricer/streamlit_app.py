import streamlit as st

# Define your pages
# The first argument is the file path, the second is the label you want in the sidebar
pg = st.navigation({
    "General": [
        st.Page("pages/home.py", title="Home", icon="🏠"),
    ],
    "Analytics Tools": [
        st.Page("pages/1_Volatility_Surfaces.py", title="Volatility Surface", icon="📈"),
        st.Page("pages/2_Asian_Option_Pricer.py", title="Asian Option Pricer", icon="🎲"),
    ]
})

st.set_page_config(page_title="Quant Dashboard", layout="wide")

# Run the selected page
pg.run()