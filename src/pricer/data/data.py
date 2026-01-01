import collections
import os
import traceback
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import requests
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestTradeRequest
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import AssetStatus, ContractType
from alpaca.trading.requests import GetOptionContractsRequest

from pricer.model.black_scholes_model import BlackScholesModel
from pricer.model.contract_model import ContractModel

# https://github.com/alpacahq/alpaca-py/blob/master/examples/options/README.md
# https://alpaca.markets/sdks/python/api_reference/trading/requests.html#getoptioncontractsrequest
# https://alpaca.markets/sdks/python/api_reference/trading/models.html#optioncontract
# https://docs.alpaca.markets/reference/corporateactions-1

class Data:
    def __init__(self):
        self.api_key = os.environ.get('ALPACA_ID')
        self.secret_key = os.environ.get('ALPACA_KEY')
        self.trade_client = TradingClient(api_key=self.api_key, secret_key=self.secret_key, paper=True, url_override=None)
        self.stock_client = StockHistoricalDataClient(self.api_key, self.secret_key)

        self.contracts_dict = {}
        self.dividend_yield_dict = collections.defaultdict(float)
        self.asset_price_dict = {}
        self.TRADING_DAYS_IN_YEAR = 252
        self.DAYS_IN_YEAR = 365

    def get_underlying_details(self, underlying_symbols: list[str]):
        corp_act_url = "https://data.alpaca.markets/v1/corporate-actions"
        headers = {
            "accept": "application/json",
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.secret_key
        }
        params = {
            "symbols": ",".join(underlying_symbols),
            "types": ["cash_dividend"],
            "start": (datetime.now() - timedelta(days=365)).date(),
            "limit": 1000
        }
        next_page = True
        while next_page:
            corp_act_resp = requests.get(corp_act_url, headers=headers, params=params).json()
            for cash_dividend in corp_act_resp["corporate_actions"].get("cash_dividends", []):
                self.dividend_yield_dict[cash_dividend["symbol"]] += cash_dividend["rate"]
            if corp_act_resp["next_page_token"]:
                params["page_token"] = corp_act_resp["next_page_token"]
            else:
                next_page = False
        request_params = StockLatestTradeRequest(symbol_or_symbols=underlying_symbols)
        latest_trades = self.stock_client.get_stock_latest_trade(request_params)
        for symbol in underlying_symbols:
            self.asset_price_dict[symbol] = latest_trades[symbol].price
            self.dividend_yield_dict[symbol] = self.dividend_yield_dict[symbol] / self.asset_price_dict[symbol]


    def get_active_options_api(self, underlying_symbols: list[str], limit: int = 1000):
        for ticker in underlying_symbols:
            all_contracts = []
            args = {
                "underlying_symbols": [ticker],
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


# d = Data()
# d.get_active_contracts_csv(["AAPL"])
# d.get_underlying_details(["TSLA"])
# d.contracts_dict["AAPL"] = d.clean_up_df(d.contracts_dict["AAPL"])
# d.contracts_dict["AAPL"].to_csv("output.csv")