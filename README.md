# pricer

```
poetry install
poetry run python -m pricer.data.data
poetry run python -m pricer.model.black_scholes_model
```

```
poetry run streamlit run src\pricer\streamlit_app.py
```

## Others

#### Notes
Black-scholes can be used to either find the fair value of an option (assuming a uniform volatility surface) or the volatility implied by its current market price. This application calculates the implied volatility given the current market price of the option and plots a 3D surface against the option's strike price and days to expiry.

To get the volatility that would give the current price, we first 

Good news, the first order derivative is the same for both PUT and CALLs.

#### Implementaion Details
- Filtering of data - happens in 2 places, the model and the data
    - data - filters based on the data that is available
      - close price is not None
      - close price is more than 5 cents - we don't want worthless options. The assumption is that the option is worthless because it is not realistic which just adds noise
      - open interest is not None
      - only OTM options 
    - model
      - moneyness - only keep options with stikes within 30% and 170% of the asset price. The others are too unrealistic
      - time to expiry - remove records which are expiring very soon. 
        - Options with < 1 week to expiry are governed by "Pin Risk" and microstructure, not standard volatility diffusion. 
        - In terms of math, the volatility formula is proportionate to the inverse of time to expiry. As time to expiry approaches 0, volatility explodes. 
      - remove options which present a simple arbitrage opportunity - probably data error
      - any volatility more than 5 is removed

#### To Do
- to use Let's Be Rational paper to calculate BS (https://vollib.org/)

#### Resources
- https://theaiquant.medium.com/mastering-the-black-scholes-model-with-python-a-comprehensive-guide-to-option-pricing-11af712697b7
- http://www.appliedbusinesseconomics.com/files/gvsnr02.pdf
