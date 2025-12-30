import os
import json
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
from model.contract_model import ContractModel

# https://github.com/alpacahq/alpaca-py/blob/master/examples/options/README.md

class Data:
    def __init__(self):
        self.api_key = os.environ.get('ALPACA_ID')
        self.secret_key = os.environ.get('ALPACA_KEY')
        self.trade_client = TradingClient(api_key=self.api_key, secret_key=self.secret_key, paper=True, url_override=None)

        self.contract_df = pd.DataFrame()
        self.underlying_symbols = ["AAPL"]

    def get_active_options_api(self):
        all_contracts = []
        args = {
            "underlying_symbols": self.underlying_symbols,
            "status": AssetStatus.ACTIVE,
            "expiration_date": None,     
            "expiration_date_gte": None, 
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
            self.args["page_token"] = res.next_page_token
            req = GetOptionContractsRequest(**args)
            res = self.trade_client.get_option_contracts(req)
            print(len(res.option_contracts))
            ls = [a for a in res.option_contracts if int(a.size) == 100 and a.close_price is not None and a.open_interest is not None]
            print(len(ls))
            self.all_contracts.extend(ls)
            if len(self.all_contracts) > 100000:
                break

        self.contract_df = pd.DataFrame([ContractModel.from_class(opt) for opt in self.all_contracts])
        self.contract_df.to_csv("df.csv")

    def get_active_contracts_csv(self):
        self.contract_df = pd.from_csv("./df.csv")