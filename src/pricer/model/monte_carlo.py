import numpy as np
from scipy.interpolate import RegularGridInterpolator, NearestNDInterpolator

class MonteCarlo:
    def __init__(self, maturities: list[list[float]], strike_prices: list[list[float]], implied_vol: list[list[float]], asset_price: float, q: float = 0, r: float = 0.035):
        self.min_maturity:float =  maturities[0][0] / 365
        self.max_maturity: float =  maturities[0][-1] / 365
        self.min_strike: float=  strike_prices[0][0]
        self.max_strike: float=  strike_prices[-1][0]
        self.maturities = np.array(maturities)
        self.strike_prices = np.array(strike_prices)
        self.implied_vol = np.array(implied_vol)
        self.asset_price = asset_price # latest underlying asset price
        self.r = r # risk free rate
        self.q = q # dividend yield

        np.savetxt("maturities.csv", self.maturities)
        np.savetxt("strike_prices.csv", self.strike_prices)
        np.savetxt("implied_vol.csv", self.implied_vol)

        print(self.min_maturity, self.max_maturity, self.min_strike, self.max_strike)

        self.lv_surface = None
        self.MAX_DISPLAY_AMT = 200

    def simple_random_walk(
        self,
        current_price: float,
        volatility: float | RegularGridInterpolator,
        strike: float,
        typ: str,
        path_length: int,
        iterations: int = 1000
    ):
        """
        Args
            currrent_price - the price of the asset at the start of the path
            volatility - used to caculate the next price in the path. If float, is constant. If interpolater, is local volatility
            strike - the strike price of the option
            typ - the type of option; either CALL or PUT
            path_length - how long to walk down each path
            iterations - how many paths to walk
        Assumption
            Observation/Fixing/Reset dates are daily EOD
        """
        generator = np.random.default_rng()
        time_delta = 1 / 252
        prices_archive = []
        payoffs = []
        for _ in range(iterations):
            prices = []
            next_price = current_price
            time_elapsed = 0
            for _ in range(path_length):
                random_var = generator.standard_normal()
                time_elapsed += time_delta
                lv = self.get_lv(time_elapsed, next_price)
                itos_correction = (lv**2) / 2
                drift_term = (self.r - itos_correction) * time_delta
                shock_term = lv * random_var * np.sqrt(time_delta)
                next_price = next_price * np.exp(drift_term + shock_term)
                prices.append(next_price)
            average_price = np.mean(prices)
            if len(prices_archive) < self.MAX_DISPLAY_AMT:
                prices_archive.append(prices.copy())
            if typ == "call":
                payoffs.append(max(0, average_price - strike))
            else:
                payoffs.append(max(0, strike - average_price))
        average_payoff = np.mean(payoffs)
        discounted_price = average_payoff * np.exp(-self.r * (path_length / 252))
        return discounted_price, np.array(prices_archive)

    def get_lv(self, t: float, k: float) -> float:
        clamped_t = np.clip(t, self.min_maturity, self.max_maturity)
        clamped_k = np.clip(k, self.min_strike, self.max_strike)
        val = self.lv_surface((clamped_k, clamped_t))
        # print("lv: ", val, "t: ", t, "k: ", k, " clamped_t: ", clamped_t, " clamped_k: ", clamped_k)
        return val

    def local_volatility(self):
        """
        Args
            maturities: interpolated maturity dates (in number of days)
            strike_prices: interpolated strike prices
            implied_vol: implied volatility surface
            asset_price: the current price of the underlying asset
            r: risk free rate
            q: dividend yield
        maturities:  maturities change within a row
            [0. , 0.5, 1. ]
            [0. , 0.5, 1. ]
            [0. , 0.5, 1. ]
        strike_prices: strike prices change within a column
            [0.,     0.,     0.]
            [0.75,   0.75,   0.75],
            [1.5,    1.5,    1.5],
        implied_vol:
            z       maturity1   maturity2   maturity3
            strike1 z11         z12         z13
            strike2 z21         z22         z23
            strik3  z31         z32         z33
        """
        print(self.maturities.shape)
        print(self.strike_prices.shape)
        print(self.implied_vol.shape)
        # 0. Set up inputs
        maturities = self.maturities / 365
        maturities_1d = maturities[0,:]
        strike_prices_1d = self.strike_prices[:,0]
        print("strike_prices_1d.shape: ", strike_prices_1d.shape)
        print("maturities_1d.shape: ", maturities_1d.shape)
        # 1. Calculate a forward price for every maturity (Ft)
        forward_price = self.asset_price * np.exp(maturities*(self.r-self.q))
        # 2. Calculate a log-moneyness for every (strike price and forward price) (y)
        y = np.log(self.strike_prices / forward_price)
        # 3. Calculate a total variance for every (variance and maturity) (w)
        w = np.pow(self.implied_vol, 2) * maturities
        # 4. Calculate Δw / Δy (this means keeping T constant) - y varies by changing its K (vertical axis)
        dw_dy = np.empty_like(w)
        for i in range(w.shape[1]):
            dw_dy[:, i] = np.gradient(w[:,i], y[:,i])
        # 5. Calculate Δw / ΔT (y constant) = Δw / ΔT (K constant) + Δw / ΔK x (r-q)K
        r_q_k = self.strike_prices * (self.r-self.q)
        dw_dk = np.gradient(w, strike_prices_1d, axis=0)
        second_term = dw_dk * r_q_k
        dw_dt_k = np.gradient(w, maturities_1d, axis=1)
        dw_dt_y = dw_dt_k + second_term
        # 6. Calculate Δ2w / Δy2 (this means keeping T constant) - y varies by changing its K (vertical axis)
        d2w_dy2 = np.empty_like(w)
        for i in range(w.shape[1]):
            d2w_dy2[:, i] = np.gradient(dw_dy[:,i], y[:,i])
        # 7. Put them all together on gatheral's equ
        numerator = dw_dt_y
        y_squared = np.pow(y,2)
        w_squared = np.pow(w,2)
        inverted_w = np.pow(w, -1)
        dw_dy_squared = np.pow(dw_dy, 2)
        denominator = 1 - (y/w * dw_dy) + (0.25 * (-0.25 - inverted_w + (y_squared / w_squared)) * dw_dy_squared) + 0.5 * d2w_dy2
        variance = numerator / denominator
        # 8. The result is variance, square root it to get volatility
        variance = np.where(variance<0, self.implied_vol**2, variance)
        np.savetxt('var.csv', variance)
        local_volatility = np.pow(variance, 0.5)
        # 9. Interpolate nan values away
        mask_invalid = np.isnan(local_volatility)
        mask_valid = ~mask_invalid

        if np.any(mask_invalid):
            print(f"Fixed {np.sum(mask_invalid)} NaN values in Local Vol surface.")
            
            # 2. Get coordinates for valid data
            # We use meshgrid to generate (Strike, Maturity) coordinates for every point
            # Note indexing='ij' to match matrix (Row, Col) convention
            X_grid, Y_grid = np.meshgrid(strike_prices_1d, maturities_1d, indexing='ij')
            
            # Extract coordinates and values of VALID points only
            valid_coords = np.column_stack((X_grid[mask_valid], Y_grid[mask_valid]))
            valid_values = local_volatility[mask_valid]
            
            # 3. Train a "Filler" interpolator
            # NearestNDInterpolator: extends valid edges into the void
            filler = NearestNDInterpolator(valid_coords, valid_values)
            
            # 4. Fill the holes
            # Get coordinates of INVALID points
            invalid_coords = np.column_stack((X_grid[mask_invalid], Y_grid[mask_invalid]))
            
            # Predict values for invalid points
            filled_values = filler(invalid_coords)
            
            # Update the main matrix
            local_volatility[mask_invalid] = filled_values
        np.savetxt('local_volatility.csv', local_volatility)
        self.lv_raw = local_volatility
        # 10. Set up an interpolater to be able to query the surface for all possible values
        local_volatility_interpolater = RegularGridInterpolator((strike_prices_1d, maturities_1d), local_volatility, bounds_error=False)
        self.lv_surface = local_volatility_interpolater
        return local_volatility_interpolater

# m = np.loadtxt("maturities.csv")
# k = np.loadtxt("strike_prices.csv")
# iv = np.loadtxt("implied_vol.csv")
# s = 272
# q = 0
# r = 0.035
# m = MonteCarlo(m,k,iv,s,q,r)
# m.local_volatility()
# px, _ = m.simple_random_walk(current_price=272,volatility=0.4,strike=280,typ="call",path_length=100, iterations=1)
# print(px)
