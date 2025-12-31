# pricer

```
poetry install
poetry run python -m pricer.data.data
poetry run python pricer.model.black_scholes_model
```

```
poetry run streamlit run src\pricer\streamlit_app.py
```

## Others

#### Notes
Black-scholes can be used to either find the fair value of an option (assuming a uniform volatility surface) or the volatility implied by its current market price. 

#### To Do
- to use Let's Be Rational paper to calculate BS (https://vollib.org/)

#### Resources
- https://theaiquant.medium.com/mastering-the-black-scholes-model-with-python-a-comprehensive-guide-to-option-pricing-11af712697b7
- http://www.appliedbusinesseconomics.com/files/gvsnr02.pdf
