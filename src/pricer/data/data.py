import os
import traceback
from datetime import datetime

import numpy as np
import pandas as pd
import yfinance as yf

from alpaca.trading.client import TradingClient
from alpaca.trading.enums import AssetStatus, ContractType
from alpaca.trading.requests import GetOptionContractsRequest

from pricer.model.black_scholes_model import BlackScholesModel
from pricer.model.contract_model import ContractModel

# https://github.com/alpacahq/alpaca-py/blob/master/examples/options/README.md
# https://alpaca.markets/sdks/python/api_reference/trading/requests.html#getoptioncontractsrequest
# https://alpaca.markets/sdks/python/api_reference/trading/models.html#optioncontract

class Data:
    def __init__(self):
        self.api_key = os.environ.get('ALPACA_ID')
        self.secret_key = os.environ.get('ALPACA_KEY')
        self.trade_client = TradingClient(api_key=self.api_key, secret_key=self.secret_key, paper=True, url_override=None)

        self.contracts_dict = {}
        self.dividend_yield_dict = {}
        self.asset_price_dict = {}
        self.TRADING_DAYS_IN_YEAR = 252
        self.DAYS_IN_YEAR = 365

    def get_underlying_details(self, underlying_symbols: list[str]):
        for symbol in underlying_symbols:
            ticker = yf.Ticker(symbol)
            self.dividend_yield_dict[symbol] = ticker.info.get("dividendYield", 0) / 100
            self.asset_price_dict[symbol] = ticker.info["previousClose"]

    def get_active_options_api(self, underlying_symbols: list[str], limit: int = 1000):
        for ticker in underlying_symbols:
            all_contracts = []
            args = {
                "underlying_symbols": underlying_symbols,
                "status": AssetStatus.ACTIVE,
                "expiration_date": None,     
                "expiration_date_gte": "2025-12-31", 
                "expiration_date_lte": None, 
                "root_symbol": None,         
                "type": None, #ContractType.CALL,   
                "style": "american",         
                "strike_price_gte": None,    
                "strike_price_lte": None,    
                "limit": 1000,                 
                "page_token": None,          
            }
            req = GetOptionContractsRequest(**args)
            res = self.trade_client.get_option_contracts(req)
            ls = [a for a in res.option_contracts if 
                    int(a.size) == 100 
                    and a.close_price is not None 
                    and a.open_interest is not None
                    and (
                        (a.strike_price > self.asset_price_dict[ticker] and a.type == ContractType.CALL) # we only want OTM options
                        or (a.strike_price < self.asset_price_dict[ticker] and a.type == ContractType.PUT)
                        )
                    and float(a.close_price) > 0.05 # filter out worthless options - assumption is that they are not realistic
                ]
            all_contracts.extend(ls)
            while res.next_page_token:
                args["page_token"] = res.next_page_token
                req = GetOptionContractsRequest(**args)
                res = self.trade_client.get_option_contracts(req)
                ls = [a for a in res.option_contracts if 
                        int(a.size) == 100 
                        and a.close_price is not None 
                        and a.open_interest is not None
                        and (
                            (a.strike_price > self.asset_price_dict[ticker] and a.type == ContractType.CALL) # we only want OTM options
                            or (a.strike_price < self.asset_price_dict[ticker] and a.type == ContractType.PUT)
                        )
                        and float(a.close_price) > 0.05 # filter out worthless options - assumption is that they are not realistic
                    ]
                all_contracts.extend(ls)
                if len(all_contracts) > limit:
                    break
            
            df = pd.DataFrame([ContractModel.from_class(opt) for opt in all_contracts])
            df = self.clean_up_df(df)
            self.contracts_dict[ticker] = df
            df.to_csv(f"{ticker}_options.csv")

    def get_active_contracts_csv(self, underlying_symbols: list[str]):
        for ticker in underlying_symbols:
            self.contracts_dict[ticker] = pd.read_csv(f"./{ticker}_options.csv")

    def clean_up_df(self, df: pd.DataFrame):
        df["expiration_date"] = pd.to_datetime(df["expiration_date"]).dt.normalize()
        df["days_to_expiry"] = (df["expiration_date"] - pd.Timestamp.now().normalize()).dt.days
        df["period_year"] = df["days_to_expiry"] / self.DAYS_IN_YEAR
        df["calculated_iv"] = df.apply(lambda row: self._calculate_iv(row), axis=1)
        df = df.dropna(subset=["calculated_iv"])

        return df

    def _calculate_iv(self, row, risk_free_rate: float = 0.035, sigma_guess: float = 0.1):
        try:
            asset_price = self.asset_price_dict[row["underlying_symbol"]]
            dividend_yield = self.dividend_yield_dict[row["underlying_symbol"]]
            black_scholes_model = BlackScholesModel(
                S=asset_price,
                d=dividend_yield,
                opt_px=row["close_price"],
                K=row["strike_price"],
                T=row["period_year"],
                r=risk_free_rate,
                typ=row["type"],
                sigma=sigma_guess
            )
            return black_scholes_model.implied_volatility()
        except:
            traceback.print_exc()
            return np.nan

if __name__ == "__main__":
    d = Data()
    d.get_active_contracts_csv(["AAPL"])
    d.get_underlying_details(["AAPL"])
    d.contracts_dict["AAPL"] = d.clean_up_df(d.contracts_dict["AAPL"])
    d.contracts_dict["AAPL"].to_csv("output.csv")