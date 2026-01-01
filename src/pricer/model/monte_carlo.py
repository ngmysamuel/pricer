import numpy as np
class MonteCarlo:
  def simple_random_walk(self, current_price: float, volatility: float, strike: float, typ: str, path_length: int, iterations: int = 1000, r: float = 0.035):
    """
    Args
        currrent_price - the price of the asset at the start of the path
        volatility - the simple random walk assumes constant volatility, used to caculate the next price in the path
        strike - the strike price of the option
        typ - the type of option; either CALL or PUT
        path_length - how long to walk down each path
        iterations - how many paths to walk
        r - risk free rate
    Assumption
        Observation/Fixing/Reset dates are daily EOD
    """
    generator = np.random.default_rng()
    time_delta = 1 / 252
    payoffs = []
    for _ in range(iterations):
        prices = []
        next_price = current_price
        for _ in range(path_length):
            random_var = generator.standard_normal()
            itos_correction = (volatility**2) / 2
            drift_term = (r - itos_correction) * time_delta
            shock_term = volatility * random_var * np.sqrt(time_delta)
            next_price = next_price * np.exp(drift_term + shock_term)
            prices.append(next_price)
        average_price = np.mean(prices)
        if typ == "call":
            payoffs.append(max(0, average_price - strike))
        else:
            payoffs.append(max(0, strike - average_price))
    average_payoff = np.mean(payoffs)
    discounted_price = average_payoff  * np.exp(-r * (path_length / 252))
    return discounted_price

m = MonteCarlo()
print(m.simple_random_walk(current_price=10,volatility=0.4,strike=10,typ="call",path_length=100))