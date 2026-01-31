# tests/conftest.py
import pytest
import numpy as np

@pytest.fixture
def flat_vol_surface():
    """
    Generates a synthetic Volatility Surface where IV is constant (20%).
    Used to verify Dupire's formula (on a flat IV surface, Local Vol == Implied Vol).
    """
    # Create a grid: 5 maturities, 5 strikes
    # Maturities (days): 30, 60, 90, 120, 150
    t_vals = np.linspace(30, 150, 5)
    # Strikes: 80 to 120
    k_vals = np.linspace(80, 120, 5)
    
    # Create lists of lists structure required by MonteCarlo.__init__
    # Each row is a strike, each column is a maturity
    
    # Maturities matrix (repeated rows)
    maturities = [t_vals.tolist() for _ in range(len(k_vals))]
    
    # Strikes matrix (repeated columns)
    strike_prices = [[k] * len(t_vals) for k in k_vals]
    
    # Implied Vol matrix (constant 0.2)
    implied_vol = [[0.2] * len(t_vals) for _ in range(len(k_vals))]
    
    return {
        "maturities": maturities,
        "strike_prices": strike_prices,
        "implied_vol": implied_vol,
        "asset_price": 100.0,
        "r": 0.05,
        "q": 0.0
    }