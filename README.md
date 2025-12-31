# pricer

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
```

## Others

### Notes
Black-scholes can be used to either find the fair value of an option (assuming a uniform volatility surface) or the volatility implied by its current market price. This application calculates the implied volatility given the current market price of the option and plots a 3D surface against the option's strike price and days to expiry.

To shift black-scholes so that the volatility becomes the subject, the first order derivative of it is required.Good news, the first order derivative is the same for both PUT and CALLs. The formula is as such:

$$\sigma =\frac{V(\sigma )-V(\hat{\sigma })+V^{\prime }(\^{\sigma })\hat{\sigma }}{V^{\prime }(\hat{\sigma })}$$

where:

$\hat{\sigma }$ is the volatility guess

$V^{\prime}$ is the first order derivative of black-scholes

$V^{\prime }(\hat{\sigma })$ thus means the first order derivative of black-scholes using the volatility guess

We start off with a guess as to where the volatility is that resulted in the current market price. Using the formula above, we can get a sigma value. Using Newton - Raphson, we can solve for the implied volatility. This is done by comparing the resulting sigma and the initial sigma guess. If they do not align, we repeat using the resulting sigma value as the guess value now. 

However, if the option has too small a vega or is near expiration, Newton - Raphson would not work. The fall back will use the bisection approach to solve for a root. Taking two maximum and minimum volatility guesses, we keep shifting solving for the option price using a midpoint sigma till we get a match with the current market value of the option. 

### Implementaion Details
- Filtering of data - happens in 2 places, the model and the data
    - data - filters based on the data that is available
      - close price is not None
      - close price is more than 5 cents
        - we don't want worthless options. The assumption is that the option is worthless because it is not realistic which just adds noise
      - open interest is not None
      - only OTM options 
    - model
      - moneyness - only keep options with stikes within 30% and 170% of the asset price. The others are too unrealistic
      - time to expiry - remove records which are expiring very soon. 
        - Options with < 1 week to expiry are governed by "Pin Risk" and microstructure, not standard volatility diffusion. 
        - In terms of math, the volatility formula is proportionate to the inverse of time to expiry. As time to expiry approaches 0, volatility explodes. 
      - remove options which present a simple arbitrage opportunity - probably data error.
        - Stock at $100. Strike price is $90. Option price now is $9.5. This is a simple arbitrage which shoudn't exist
        - a person who buys the option and exercises it will get the stock $0.5 cheaper than buying on the open market
      - any volatility more than 5 is removed
        - affects the overall scaling of the surface graph

### To Do
- to use Let's Be Rational paper to calculate BS (https://vollib.org/)
- use Brent's Method (brentq) rather than just bisection

### Resources
- https://theaiquant.medium.com/mastering-the-black-scholes-model-with-python-a-comprehensive-guide-to-option-pricing-11af712697b7
- http://www.appliedbusinesseconomics.com/files/gvsnr02.pdf
- https://brilliant.org/wiki/newton-raphson-method/
- https://brilliant.org/wiki/root-approximation-bisection/
