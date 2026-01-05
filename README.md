# pricer

<h3 align="center"> ⚠ Work in progress ⚠</h3>
<p align="center"> You might notice some formatting issues / lack of documentation in the meantime.</p>

## How to run

### Cloud
Visit https://pricer-py.streamlit.app/

### Local
```
git clone https://github.com/ngmysamuel/pricer.git
cd pricer
poetry install
poetry run streamlit run src\pricer\streamlit_app.py
```

```
poetry run python -m pricer.data.data
poetry run python -m pricer.model.black_scholes_model
poetry run python -m pricer.model.monte_carlo
```

## Notes

### Black Scholes Implied Volatility

Black-scholes can be used to either find the fair value of an option (assuming a uniform volatility surface) or the volatility implied by its current market price. This application calculates the implied volatility given the current market price of the option and plots a 3D surface against the option's strike price and days to expiry.

To shift black-scholes so that the volatility becomes the subject, the first order derivative of it is required.Good news, the first order derivative is the same for both PUT and CALLs. The formula is as such:

$$\sigma =\frac{V(\sigma )-V(\hat{\sigma })+V^{\prime }(\hat{\sigma })\hat{\sigma }}{V^{\prime }(\hat{\sigma })}$$

where:

$\hat{\sigma }$ is the volatility guess

$V^{\prime}$ is the first order derivative of black-scholes

$V^{\prime }(\hat{\sigma })$ thus means the first order derivative of black-scholes using the volatility guess

We start off with a guess as to where the volatility is that resulted in the current market price. Using the formula above, we can get a sigma value. Using Newton - Raphson, we can solve for the implied volatility. This is done by comparing the resulting sigma and the initial sigma guess. If they do not align, we repeat using the resulting sigma value as the guess value now. 

However, if the option has too small a vega or is near expiration, Newton - Raphson would not work. The fall back will use the bisection approach to solve for a root. Taking two maximum and minimum volatility guesses, we keep shifting solving for the option price using a midpoint sigma till we get a match with the current market value of the option. 

### Local Volatility 

For pricing an Asian Option, we make use of the IV surface derived above and converting it to a local volatility (LV) surface which allows us to walk down the price path with more accuracy.

Dupire's Formula in relation to IV (Gatheral, 2006, p. 11)

$$v_L(y, T) = \frac{\frac{\partial w}{\partial T}}{1 - \frac{y}{w} \frac{\partial w}{\partial y} + \frac{1}{4} \left( -\frac{1}{4} - \frac{1}{w} + \frac{y^2}{w^2} \right) \left( \frac{\partial w}{\partial y} \right)^2 + \frac{1}{2} \frac{\partial^2 w}{\partial y^2}}$$

where:

| Terms      | Terms |
| ----------- | ----------- |
| $T$ is the period in years| $S_0$ is the underlying asset's price|
| $K$ is the strike price| $r$ is the risk free rate|
|$q$ is the dividend rate|$\sigma$ is the implied volatility|

|Compound Terms|
|-|
|$F_T = S_0e^{(r-q)T}$|
|$y = ln(\frac{K}{F_T})$|
|$w = \sigma^2T$|

|Derivative|Notes|
|-|-|
|$\frac{\partial w}{\partial y}$|Taken as the change in w divided by the change in y, $\frac{\Delta w}{\Delta y}$, while keeping $T$ constant. This derivative can be calculated as is because we have the means to keep $T$ constant while varying $w$ and $y$ - going down the columns of the matrix ensures maturity is not changing|
|$\frac{\partial w}{\partial T}$|Taken as the change in w divided by the change in y, $\frac{\Delta w}{\Delta T}$, while keeping $y$ constant. This thus, is problematic because $y$ cannot be kept constant while varying $T$. This can be manipulated into $\frac{\Delta w}{\Delta T}_K + \frac{\Delta w}{\Delta K}_T \cdot (r-q)K$. This derivation is left as an exercise to the reader. (kidding, see below for the derivation). Note the subscript $_x$ represents what is kept constant. |
|$\frac{\partial^2 w}{\partial y^2}$| Similar to the above but make use of $\frac{\Delta w}{\Delta y}$'s gradient while still keeping $T$ unchanging.|

|Grids of variables|Notes|
|-|-|
|Maturity|1D varies along the horizontal (increases →) |
|Strike| 1D varies along the vertical (increases ↓)|
|$\sigma$|2D varies along both horizontal and verical (increases → & ↓)|
|$w$|2D varies along both horizontal and verical (increases → & ↓)|
|$F_T$|1D varies along the horizontal (increases →) |
|$y$|2D varies along both horizontal and verical (increases → & ↓)|

#### Derivation of $\frac{\partial w}{\partial T}$

The total derivative of $\frac{\partial w}{\partial T}$ can be written as (note subscript $_x$ represents the value being kept constant)

$$\frac{\partial w}{\partial T}_y = \frac{\partial w}{\partial K} \cdot \frac{\partial K}{\partial T} + \frac{\partial w}{\partial T}_K \cdot \frac{\partial T}{\partial T}$$

Simplify away $\frac{\partial T}{\partial T} = 1$, giving __Equation 1__

$$\frac{\partial w}{\partial T}_y = \frac{\partial w}{\partial K} \cdot \frac{\partial K}{\partial T} + \frac{\partial w}{\partial T}_K$$

$\frac{\partial w}{\partial T}_K$ and $\frac{\partial w}{\partial K}$ is known; this leaves $\frac{\partial K}{\partial T}$ to be found. Zoom in on the formula for $y$ - why y? A clue is that $\frac{\partial K}{\partial T}$ is needed while having $y$ remain constant

$$y = ln(\frac{K}{F_T})$$

Substitute in $F_T$ and simplify the $ln$ terms

$$y = ln(K) - ln(S_0e^{(r-q)T})$$
$$y = ln(K) - (r-q)T - ln(S_0)$$

Rearrange the formula to get K as the subject (objective is to differentiate K after all), giving __Equation 2__

$$ln(K) = y + (r-q)T + ln(S_0)$$
$$K = \exp(y + ln(S_0) + (r-q)T)$$
$$K = e^y \cdot S_0 \cdot e^{(r-q)T}$$

Differentiate K with respect to T

$$\frac{\partial K}{\partial T} = e^y \cdot S_0 \cdot (r-q)e^{(r-q)T}$$
$$\frac{\partial K}{\partial T} = e^y \cdot S_0 \cdot e^{(r-q)T} \cdot (r-q)$$

Notice that the first 3 terms equal $K$ as seen in __Equation 2__. Substitute in that value, giving __Equation 3__

$$\frac{\partial K}{\partial T} = K \cdot (r-q)$$

Substitute __Equation 3__ into __Equation 1__

$$\frac{\partial w}{\partial T}_y = \frac{\partial w}{\partial K} \cdot \frac{\partial K}{\partial T} + \frac{\partial w}{\partial T}_K$$
$$\frac{\partial w}{\partial T}_y = \frac{\partial w}{\partial K} \cdot (K(r-q)) + \frac{\partial w}{\partial T}_K$$

#### Intuition
We are looking for change in $w$ and change in $T$ while keeping all other variables including $y$ and $K$ constant.

Say we are keeping $K$ constant as we tweak $T$. $y$ continue to moves due to the $(r-q)T$ term in the exponential 

We need to then also tweak $K$ to ensure it keeps pace - leaving $y$ unchanging.

That $K$ tweak is $K(r-q)$

### Implementaion Details
- Filtering of data - happens in 2 places, the model and the data
    - data - filters based on the data that is available
      - close price is not None
      - close price is more than 5 cents
        - we don't want worthless options. The assumption is that the option is worthless because it is not realistic which just adds noise
      - open interest is not None
      - only OTM options - both PUTs and CALLs
    - model
      - moneyness - only keep options with stikes within 30% and 170% of the asset price. The others are too unrealistic
      - time to expiry - remove records which are expiring very soon. 
        - Options with < 1 week to expiry are governed by "Pin Risk" and microstructure, not standard volatility diffusion. 
        - In terms of math, the volatility formula is proportionate to the inverse of time to expiry. As time to expiry approaches 0, volatility explodes. 
      - remove options which present a simple arbitrage opportunity - probably data error.
        - Stock at $100. Strike price is $90. Option price now is $9.5. This is a simple arbitrage which shoudn't exist
        - a person who buys the option and exercises it will get the stock $0.5 cheaper than buying on the open market
      - any volatility more than 3 is removed
        - affects the overall scaling of the surface graph
- Timing issues
    - black-scholes is calculated using the number of calendar days till expiry i.e. options expiring in hours (not days) will be 0/365
    - we filter out options close to expiry so no issue with the above
    - but if we do need to include, will need to use seconds instead

## To Do
### Black - Scholes
- To use Let's Be Rational paper to calculate BS (https://vollib.org/)
- Use Brent's Method (brentq) rather than just bisection
- Live update of options data, implied volatility surface
### Monte - Carlo
- Use Milstein instead of Brownian (https://quant.stackexchange.com/q/30362)
- Use control variates
- Smoothen the IV surface - SVI parameterization
### Others
- Value European and American Options using trinomial trees (https://essay.utwente.nl/fileshare/file/59223/scriptie__R_van_der_Kamp.pdf)
- Rewrite math in C++/Rust

## Resources
### Black - Scholes
- https://theaiquant.medium.com/mastering-the-black-scholes-model-with-python-a-comprehensive-guide-to-option-pricing-11af712697b7
- http://www.appliedbusinesseconomics.com/files/gvsnr02.pdf
- https://brilliant.org/wiki/newton-raphson-method/
- https://brilliant.org/wiki/root-approximation-bisection/
### Monte - Carlo
#### Random Walk (Brownian)
- https://www.investopedia.com/articles/07/montecarlo.asp (Euler-Maruyama Discretization)
- https://quant.stackexchange.com/q/17032 (expected return is the risk free rate)
- https://quant.stackexchange.com/q/4589 (Geometric Brownian)
#### Local Volatility
- https://medium.com/@abatrek059/local-volatility-surface-exotic-options-pricing-an-example-1caa3cf1ed89
- https://financetrainingcourse.com/education/2014/05/implied-and-local-volatility-surfaces-in-excel-final-steps/
- Gatheral, J. (2006). The volatility surface: A Practitioner’s Guide. Wiley.