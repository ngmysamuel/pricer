import numpy as np
import scipy.stats as si

class BlackScholesModel:
    """
    Validated with https://www.quantpie.co.uk/oup/oup_bsm_price_greeks.php
    """
    def __init__(self, S, d, opt_px, K, T, r, sigma = None):
        self.S = S                     # Underlying asset price
        self.d = d                     # Underlying asset dividend yield
        self.option_price  = opt_px    # price of the option
        self.K = K                     # Option strike price
        self.T = T                     # Time to expiration in years
        self.r = r                     # Risk-free interest rate
        self.sigma = sigma             # Volatility of the underlying asset (when calculating IV, this is a guess)

    def d1(self):
        return (np.log(self.S / self.K) + (self.r - self.d + 0.5 * self.sigma ** 2) * self.T) / (self.sigma * np.sqrt(self.T))
    
    def d2(self):
        return self.d1() - self.sigma * np.sqrt(self.T)
    
    def call_option_price(self):
        return ((self.S * np.exp(-self.d * self.T)) * si.norm.cdf(self.d1(), 0.0, 1.0) - self.K * np.exp(-self.r * self.T) * si.norm.cdf(self.d2(), 0.0, 1.0))

    def call_option_price_derivative(self):
        return self.S * np.sqrt(self.T) * np.exp(-self.d * self.T) * np.power(np.sqrt(2 * np.pi), -1) * np.exp(-0.5 * np.power(self.d1(),2))
    
    def put_option_price(self):
        return (self.K * np.exp(-self.r * self.T) * si.norm.cdf(-self.d2(), 0.0, 1.0) - self.S * si.norm.cdf(-self.d1(), 0.0, 1.0))

    def implied_volatility(self):
        sigma_guess, implied_sigma, to_continue = self.sigma, float("inf"), True
        while to_continue:
            implied_sigma = (self.option_price - self.call_option_price() + (self.call_option_price_derivative() * sigma_guess)) / self.call_option_price_derivative()
            to_continue = abs(sigma_guess-implied_sigma) > 1E-3
            print(sigma_guess, " ", implied_sigma)
            sigma_guess = implied_sigma
        return sigma_guess

bs = BlackScholesModel(10, 0.0, 1.9174, 12, 2, 0.05, 0.1)
print(bs.call_option_price())
print(bs.call_option_price_derivative())
print(bs.implied_volatility())