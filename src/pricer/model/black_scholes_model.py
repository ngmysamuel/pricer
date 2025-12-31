import numpy as np
import scipy.stats as si
from typing import Optional

class BlackScholesModel:
    """
    Validated with
    https://www.quantpie.co.uk/oup/oup_bsm_price_greeks.php
    https://www.option-price.com/implied-volatility.php
    """
    def __init__(self, S: float, d: float, opt_px: float, K: float, T: float, r: float, typ: str, sigma: float = None):
        self.S = S                     # Underlying asset price
        self.d = d                     # Underlying asset dividend yield
        self.option_price  = opt_px    # price of the option
        self.K = K                     # Option strike price
        self.T = T                     # Time to expiration in years
        self.r = r                     # Risk-free interest rate
        self.type = typ                # PUT or CALL option
        self.sigma = sigma             # Volatility of the underlying asset (when calculating IV, this is a guess)
        self.SIGMA_UPPER_LIMIT = 5
        self.SIGMA_LOWER_LIMIT = 0.001
        self.MAX_ITERATIONS = 250
        self.TIME_CAP = 7
        self.MAX_VOL = 5

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

    def first_order_derivative(self, sigma: Optional[float] = None):
        if sigma is None:
            sigma = self.sigma
        return self.S * np.sqrt(self.T) * np.exp(-self.d * self.T) * np.power(np.sqrt(2 * np.pi), -1) * np.exp(-0.5 * np.power(self.d1(sigma),2))
    
    def put_option_price(self, sigma: Optional[float] = None):
        if sigma is None:
            sigma = self.sigma
        return (self.K * np.exp(-self.r * self.T) * si.norm.cdf(-self.d2(sigma), 0.0, 1.0) - (self.S * np.exp(-self.d * self.T)) * si.norm.cdf(-self.d1(sigma), 0.0, 1.0))

    def implied_volatility(self):
        """
        Attempt to solve using Newton - Raphson. If not solvable, use bisection approach.
        """
        # Clean the data
        if self.type == "call":
            lower_bound = max(0, self.S * np.exp(-self.d * self.T) - self.K * np.exp(-self.r * self.T))
        else:
            lower_bound = max(0, self.K * np.exp(-self.r * self.T) - self.S * np.exp(-self.d * self.T))
        upper_bound = self.S * np.exp(-self.d * self.T)
        if self.option_price < lower_bound or self.option_price > upper_bound: # impossible for an option to be worth more than buying the stock on open market (arbitrage)
            return np.nan
        if self.T < (self.TIME_CAP/365): # remove records with less than TIME_CAP days to expiry
            return np.nan
        moneyness = self.K / self.S # Ratio of Strike to Spot
        if moneyness < 0.3 or moneyness > 1.7: # Filter: Only keep strikes within 30% to 170% of Spot Price
            return np.nan
        # Calculate Implied Volatility
        vol = self._newton_raphson()
        if vol is None:
            vol = self._bisection()
        if vol > self.MAX_VOL:
            return np.nan
        return vol

    def _bisection(self):
        """
        Working on a monotonic slope - increasing volatility will have increasing option price
        """
        # print("bisection")
        # print(self.S, self.d, self.option_price, self.K, self.T, self.r, self.sigma)
        sigma_lower, sigma_upper = self.SIGMA_LOWER_LIMIT, self.SIGMA_UPPER_LIMIT
        implied_price = float("inf")
        for _ in range(self.MAX_ITERATIONS):
            sigma_mid = (sigma_lower + sigma_upper) / 2
            implied_price = self.call_option_price(sigma_mid) if self.type == "call" else self.put_option_price(sigma_mid)
            if abs(implied_price - self.option_price) < 1E-5:
                return sigma_mid
            if implied_price < self.option_price:
                sigma_lower = sigma_mid
            elif implied_price > self.option_price:
                sigma_upper = sigma_mid
        return np.nan

    def _newton_raphson(self):
        sigma_guess, implied_sigma, to_continue = self.sigma, float("inf"), True
        while to_continue:
            vega = self.first_order_derivative(sigma_guess)
            if abs(vega) < 1E-8:
                return None
            implied_price = self.call_option_price(sigma_guess) if self.type == "call" else self.put_option_price(sigma_guess)
            implied_sigma = (self.option_price - implied_price + (vega * sigma_guess)) / vega
            if implied_sigma <= 0:
                return None
            to_continue = abs(sigma_guess-implied_sigma) > 1E-5
            sigma_guess = implied_sigma
        return sigma_guess

# bs = BlackScholesModel(S=10, d=0.0, opt_px=1.9174, K=12, T=2, r=0.05, typ="call", sigma=0.1) # Newton-Raphson
# bs = BlackScholesModel(S=50, d=0.0, opt_px=0.10, K=80, T=0.019178, r=0.05, typ="call", sigma=0.1) # bisection
# bs = BlackScholesModel(S=273.76, d=0.0038, opt_px=153.88, K=120.0, T=0.0027397260273972603, r=0.035, typ="call", sigma=0.1) # bisection - sigma limit > 5
# bs = BlackScholesModel(S=273.76, d=0.0038, opt_px=33.85, K=240.0, T=0.024657534246575342, r=0.035, typ="call", sigma=0.1) # bisection - impossible cases are filtered out
# bs = BlackScholesModel(S=273.76, d=0.0038, opt_px=270.3, K=5.0, T=0.043835616438356165, r=0.035, typ="call", sigma=0.1) # bisection - sigma limit > 5
# print(bs.call_option_price())
# print(bs.first_order_derivative())
# print(bs.implied_volatility())