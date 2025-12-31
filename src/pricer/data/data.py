import os
import json
import traceback
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from time import time
import pandas as pd
from alpaca.trading.client import TradingClient
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.data.historical.option import OptionHistoricalDataClient
from alpaca.trading.stream import TradingStream
from alpaca.data.live.option import OptionDataStream
from alpaca.data.requests import (
    OptionBarsRequest,
    OptionTradesRequest,
    OptionLatestQuoteRequest,
    OptionLatestTradeRequest,
    OptionSnapshotRequest,
    OptionChainRequest    
)
from alpaca.trading.requests import (
    GetOptionContractsRequest,
    GetAssetsRequest,
    MarketOrderRequest,
    GetOrdersRequest,
    ClosePositionRequest
)
from alpaca.trading.enums import (
    AssetStatus,
    ExerciseStyle,
    OrderSide,
    OrderType,
    TimeInForce,
    QueryOrderStatus,
    ContractType
)
from alpaca.common.exceptions import APIError
from pricer.model.contract_model import ContractModel
import numpy as np
import yfinance as yf
from pricer.model.black_scholes_model import BlackScholesModel
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
            self.dividend_yield_dict[symbol] = ticker.info["dividendYield"] / 100
            self.asset_price_dict[symbol] = ticker.info["previousClose"]
            print(self.dividend_yield_dict)
            print(self.asset_price_dict)

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
                "type": ContractType.CALL,   
                "style": "american",         
                "strike_price_gte": None,    
                "strike_price_lte": None,    
                "limit": 1000,                 
                "page_token": None,          
            }
            req = GetOptionContractsRequest(**args)
            res = self.trade_client.get_option_contracts(req)
            ls = [a for a in res.option_contracts if int(a.size) == 100 and a.close_price is not None and a.open_interest is not None]
            all_contracts.extend(ls)
            while res.next_page_token:
                args["page_token"] = res.next_page_token
                req = GetOptionContractsRequest(**args)
                res = self.trade_client.get_option_contracts(req)
                print(len(res.option_contracts))
                ls = [a for a in res.option_contracts if int(a.size) == 100 and a.close_price is not None and a.open_interest is not None]
                print(len(ls))
                all_contracts.extend(ls)
                if len(all_contracts) > limit:
                    break
            
            df = pd.DataFrame([ContractModel.from_class(opt) for opt in all_contracts])
            df.to_csv(f"{ticker}_options.csv")
            self.contracts_dict[ticker] = self.clean_up_df(df)
        

    def get_active_contracts_csv(self, underlying_symbols: list[str]):
        for ticker in underlying_symbols:
            self.contracts_dict[ticker] = pd.read_csv(f"./{ticker}_options.csv")

    def clean_up_df(self, df: pd.DataFrame):
        df["expiration_date"] = pd.to_datetime(df["expiration_date"])
        df["days_to_expiry"] = (df["expiration_date"] - datetime.now()).dt.days
        df["period_year"] = df["days_to_expiry"] / self.DAYS_IN_YEAR
        df["calculated_iv"] = df.apply(lambda row: self._calculate_iv(row), axis=1)
        df = df.dropna(subset=["calculated_iv"])

        return df

    def _calculate_iv(self, row, risk_free_rate: float = 0.035, sigma_guess: float = 0.1):
        try:
            # print(row)
            asset_price = self.asset_price_dict[row["underlying_symbol"]]
            dividend_yield = self.dividend_yield_dict[row["underlying_symbol"]]
            black_scholes_model = BlackScholesModel(
                S=asset_price,
                d=dividend_yield,
                opt_px=row["close_price"],
                K=row["strike_price"],
                T=row["period_year"],
                r=risk_free_rate,
                sigma=sigma_guess
            )
        except Exception as e:
            print(1)
            traceback.print_exc()
            return np.nan
        try:
            return black_scholes_model.implied_volatility()
        except Exception as e:
            print(2)
            traceback.print_exc()
            return np.nan

if __name__ == "__main__":
    d = Data()
    d.get_active_contracts_csv(["AAPL"])
    d.get_underlying_details(["AAPL"])
    d.contracts_dict["AAPL"] = d.clean_up_df(d.contracts_dict["AAPL"])
    d.contracts_dict["AAPL"].to_csv("output.csv")