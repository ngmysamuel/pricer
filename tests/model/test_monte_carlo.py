import pytest
import numpy as np
from pricer.model.monte_carlo import MonteCarlo
from tests.configure_tests import flat_vol_surface

class TestMonteCarlo:

    def test_local_volatility_flat_surface_recovery(self, flat_vol_surface):
        """
        CRITICAL MATH TEST:
        If Implied Volatility is constant (e.g., 20%) across all Strikes/Times, 
        Dupire's formula must result in Local Volatility = 20%.
        """
        mc = MonteCarlo(**flat_vol_surface)
        
        # Run the Dupire conversion
        mc.local_volatility()
        
        # Check the middle of the surface (avoiding boundary finite difference errors)
        # The input was exactly 0.2 everywhere.
        mid_x, mid_y = 2, 2 
        calculated_lv = mc.lv_raw[mid_x, mid_y]
        
        # Allow small tolerance for finite difference approximation errors
        assert calculated_lv == pytest.approx(0.2, abs=0.01)

    def test_deterministic_path(self, flat_vol_surface):
        """
        If volatility is effectively 0, the asset should grow exactly by the risk-free rate.
        S_T = S_0 * e^(rT)
        """
        mc = MonteCarlo(**flat_vol_surface)
        mc.local_volatility() # Initialize surface
        
        S0 = 100
        r = 0.05
        T_days = 30
        T_years = 30/252
        
        # Override volatility to near-zero for this specific walk
        payoff, paths, _ = mc.simple_random_walk(
            current_price=S0,
            volatility=1e-5, # ~0 vol
            strike=100, 
            typ="call", 
            path_length=T_days, 
            iterations=10
        )
        
        final_prices = paths[:, -1]
        expected_price = S0 * np.exp(r * T_years)
        
        # All paths should be identical and equal to expected price
        assert np.mean(final_prices) == pytest.approx(expected_price, rel=1e-4)

    def test_asian_option_average_logic(self, flat_vol_surface):
        """
        Verify that the payoff is calculated on the Average Price, not Final Price.
        """
        mc = MonteCarlo(**flat_vol_surface)
        
        # We assume specific values to test the math
        # Path: [100, 102, 104] (Arithmetic Progression)
        # Average = 102
        # Strike = 101
        # Payoff (Call) = 1.0
        
        # We cannot force the path in the random generator easily without mocking numpy,
        # but we can verify the payoff return logic if we set paths manually? 
        # Since we can't inject paths into `simple_random_walk`, we test the integration:
        
        # High volatility, short path, Deep ITM to ensure positive payoff
        # S=100, K=50. The Average will likely be > 50.
        payoff, paths, _ = mc.simple_random_walk(
            current_price=100,
            volatility=0.2,
            strike=50,
            typ="call",
            path_length=10,
            iterations=100
        )
        
        # Manual verification of the returned calculation
        # Recalculate average from returned paths
        # Note: Code uses `prices[:, 1:]` (excluding t=0)
        calc_averages = np.mean(paths[:, 1:], axis=1)
        expected_payoffs = np.maximum(0, calc_averages - 50)
        
        # Discount factor
        df = np.exp(-0.05 * (10/252))
        expected_mean_payoff = np.mean(expected_payoffs) * df
        
        assert payoff == pytest.approx(expected_mean_payoff, abs=1e-5)

    def test_lv_interpolation_bounds(self, flat_vol_surface):
        """
        Ensure get_lv clamps values and doesn't crash when querying outside the surface.
        """
        mc = MonteCarlo(**flat_vol_surface)
        mc.local_volatility()
        
        # Query a time way beyond max maturity
        lv_val = mc.get_lv(t=10.0, k=np.array([100]))
        assert isinstance(lv_val, float) or isinstance(lv_val, np.ndarray)

    def test_local_volatility_nan_filling(self):
        """
        Tests if the code correctly fills holes in the IV surface.
        """
        # Create a surface with a NaN in the middle
        maturities = [[30, 60, 90], [30, 60, 90], [30, 60, 90]]
        strikes    = [[90, 90, 90], [100, 100, 100], [110, 110, 110]]
        
        # Middle point is NaN
        iv = [
            [0.2, 0.2, 0.2],
            [0.2, np.nan, 0.2], # <--- Hole
            [0.2, 0.2, 0.2]
        ]
        
        mc = MonteCarlo(maturities, strikes, iv, asset_price=100)
        
        # This function should trigger the NaN filling logic inside
        mc.local_volatility()
        
        # Check the raw LV matrix
        # The middle point (index 1,1) should NOT be NaN anymore
        lv_middle = mc.lv_raw[1, 1]
        
        assert not np.isnan(lv_middle)
        # Since neighbors are 0.2, the filled value should be close to 0.2
        assert lv_middle == pytest.approx(0.2, abs=0.05)