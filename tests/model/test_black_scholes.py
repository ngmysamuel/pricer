import pytest
import numpy as np
from pricer.model.black_scholes_model import BlackScholesModel

class TestBlackScholes:
    
    def test_call_price_benchmark(self):
        """
        Validates against a standard textbook example.
        S=100, K=100, T=1, r=0.05, sigma=0.2
        Expected Call Price ~ 10.4506
        """
        bs = BlackScholesModel(S=100, d=0, opt_px=0, K=100, T=1, r=0.05, typ="call", sigma=0.2)
        price = bs.call_option_price()
        assert price == pytest.approx(10.4506, abs=1e-4)

    def test_put_call_parity(self):
        """
        Verifies: C - P = S*e^(-dT) - K*e^(-rT)
        """
        S, K, T, r, d, sigma = 100, 110, 0.5, 0.05, 0.02, 0.3
        
        bs_c = BlackScholesModel(S=S, d=d, opt_px=0, K=K, T=T, r=r, typ="call", sigma=sigma)
        bs_p = BlackScholesModel(S=S, d=d, opt_px=0, K=K, T=T, r=r, typ="put", sigma=sigma)
        
        call_px = bs_c.call_option_price()
        put_px = bs_p.put_option_price()
        
        lhs = call_px - put_px
        rhs = (S * np.exp(-d * T)) - (K * np.exp(-r * T))
        
        assert lhs == pytest.approx(rhs, abs=1e-5)

    def test_implied_vol_convergence(self):
        """
        Round-trip test:
        1. Calculate price from known Sigma (0.25).
        2. Feed price back into model with unknown Sigma.
        3. Assert calculated Implied Volatility == 0.25.
        """
        target_vol = 0.25
        bs_ref = BlackScholesModel(S=100, d=0, opt_px=0, K=100, T=1, r=0.05, typ="call", sigma=target_vol)
        fair_price = bs_ref.call_option_price()
        
        bs_solver = BlackScholesModel(S=100, d=0, opt_px=fair_price, K=100, T=1, r=0.05, typ="call", sigma=0.1)
        calculated_vol = bs_solver.implied_volatility()
        
        assert calculated_vol == pytest.approx(target_vol, abs=1e-4)

    def test_arbitrage_checks(self):
        """
        Test that impossible prices return NaN for IV.
        Call Price cannot exceed Stock Price.
        """
        # Price is 105, Stock is 100. Impossible.
        bs = BlackScholesModel(S=100, d=0, opt_px=105, K=100, T=1, r=0.05, typ="call")
        assert np.isnan(bs.implied_volatility())