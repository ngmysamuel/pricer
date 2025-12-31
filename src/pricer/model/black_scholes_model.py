import numpy as np
import scipy.stats as si
from typing import Optional

class BlackScholesModel:
    """
    Validated with
    https://www.quantpie.co.uk/oup/oup_bsm_price_greeks.php
    https://www.option-price.com/implied-volatility.php
    """
    def __init__(self, S, d, opt_px, K, T, r, sigma = None):
        self.S = S                     # Underlying asset price
        self.d = d                     # Underlying asset dividend yield
        self.option_price  = opt_px    # price of the option
        self.K = K                     # Option strike price
        self.T = T                     # Time to expiration in years
        self.r = r                     # Risk-free interest rate
        self.sigma = sigma             # Volatility of the underlying asset (when calculating IV, this is a guess)

    def d1(self, sigma: Optional[float] = None):
        if sigma is None:
            sigma = self.sigma
        return (np.log(self.S / self.K) + (self.r - self.d + 0.5 * sigma ** 2) * self.T) / (sigma * np.sqrt(self.T))
    
    def d2(self, sigma: Optional[float] = None):
        if sigma is None:
            sigma = self.sigma
        return self.d1(sigma) - sigma * np.sqrt(self.T)
    
    def call_option_price(self, sigma: Optional[float] = None):
        if sigma is None:
            sigma = self.sigma
        return ((self.S * np.exp(-self.d * self.T)) * si.norm.cdf(self.d1(sigma), 0.0, 1.0) - self.K * np.exp(-self.r * self.T) * si.norm.cdf(self.d2(sigma), 0.0, 1.0))

    def call_option_price_derivative(self, sigma: Optional[float] = None):
        if sigma is None:
            sigma = self.sigma
        return self.S * np.sqrt(self.T) * np.exp(-self.d * self.T) * np.power(np.sqrt(2 * np.pi), -1) * np.exp(-0.5 * np.power(self.d1(sigma),2))
    
    def put_option_price(self, sigma: Optional[float] = None):
        if sigma is None:
            sigma = self.sigma
        return (self.K * np.exp(-self.r * self.T) * si.norm.cdf(-self.d2(sigma), 0.0, 1.0) - self.S * si.norm.cdf(-self.d1(sigma), 0.0, 1.0))

    def implied_volatility(self):
        """
        Attempt to solve using Newton - Raphson. If not solvable, use bisection approach.
        """
        # Clean the data
        lower_bound = max(0, self.S * np.exp(-self.d * self.T) - self.K * np.exp(-self.d * self.T))
        upper_bound = self.S * np.exp(-self.d * self.T)
        if self.option_price < lower_bound or self.option_price > upper_bound:
            return np.nan
        vol = self._newton_raphson()
        if vol is not None:
            return vol
        return self._bisection()

    def _bisection(self):
        """
        Working on a monotonic slope - increasing volatility will have increasing option price
        """
        sigma_lower, sigma_upper = 0.001, 5
        implied_price = float("inf")
        while abs(implied_price - self.option_price) > 1E-5:
            sigma_mid = (sigma_lower + sigma_upper) / 2
            implied_price = self.call_option_price(sigma_mid)
            if implied_price < self.option_price:
                sigma_lower = sigma_mid
            elif implied_price > self.option_price:
                sigma_upper = sigma_mid
        return sigma_mid
            

    def _newton_raphson(self):
        sigma_guess, implied_sigma, to_continue = self.sigma, float("inf"), True
        while to_continue:
            vega = self.call_option_price_derivative(sigma_guess)
            if vega < 1E-8:
                return
            implied_sigma = (self.option_price - self.call_option_price(sigma_guess) + (vega * sigma_guess)) / vega
            to_continue = abs(sigma_guess-implied_sigma) > 1E-5
            sigma_guess = implied_sigma
        return sigma_guess

# bs = BlackScholesModel(S=10, d=0.0, opt_px=1.9174, K=12, T=2, r=0.05, sigma=0.1) # Newton-Raphson
# bs = BlackScholesModel(S=50, d=0.0, opt_px=0.10, K=80, T=0.019178, r=0.05, sigma=0.1) # bisection
# print(bs.call_option_price())
# print(bs.call_option_price_derivative())
# print(bs.implied_volatility())