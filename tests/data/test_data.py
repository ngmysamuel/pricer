import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pricer.data.data import Data
import collections

# --- Fixtures ---

@pytest.fixture
def mock_alpaca_env(monkeypatch):
    """
    monkeypatch is a built-in pytest fixture to set env vars safely.
    """
    monkeypatch.setenv("ALPACA_ID", "TEST_API_KEY")
    monkeypatch.setenv("ALPACA_KEY", "TEST_SECRET_KEY")

@pytest.fixture
def data_instance(mocker, mock_alpaca_env):
    """
    Returns a Data instance with mocked internal clients.
    """
    # Patch the classes so they don't connect to the internet
    mocker.patch("pricer.data.data.TradingClient")
    mocker.patch("pricer.data.data.StockHistoricalDataClient")
    
    d = Data()

    d.asset_price_dict = {}
    d.dividend_yield_dict = collections.defaultdict(float) 

    return d

# --- Tests ---

class TestDataProcessing:
    
    def test_calculate_iv_valid_row(self, data_instance):
        symbol = "AAPL"
        data_instance.asset_price_dict[symbol] = 150.0
        data_instance.dividend_yield_dict[symbol] = 0.01

        row = pd.Series({
            "underlying_symbol": symbol,
            "close_price": 10.0,
            "strike_price": 155.0,
            "period_year": 0.5,
            "type": "call",
            "style": "american"
        })

        iv = data_instance._calculate_iv(row)
        
        # Pytest assertion style
        assert isinstance(iv, float)
        assert not np.isnan(iv)
        assert iv > 0

    def test_clean_up_df_logic(self, data_instance, mocker):
        # Setup data
        data_instance.asset_price_dict = {"TEST": 100.0}
        data_instance.dividend_yield_dict = {"TEST": 0.0}
        future_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
        
        df = pd.DataFrame([
            {
                "underlying_symbol": "TEST",
                "expiration_date": future_date,
                "strike_price": 110,
                "close_price": 5.0,
                "type": "call", 
                "style": "american",
                "open_interest": 100,
                "size": 100
            }
        ])

        # Mock the internal _calculate_iv method to return a fixed float
        # This isolates the test to just the dataframe cleaning logic
        mocker.patch.object(data_instance, '_calculate_iv', return_value=0.25)

        cleaned_df = data_instance.clean_up_df(df)

        assert len(cleaned_df) == 1
        assert cleaned_df.iloc[0]["period_year"] == pytest.approx(1.0, abs=0.01)
        assert cleaned_df.iloc[0]["calculated_iv"] == 0.25

class TestApiInteraction:
    
    def test_get_underlying_details_dividends(self, data_instance, mocker):
        symbol = "DIV_STOCK"
        price = 100.0
        
        # 1. Mock the Stock Client response
        mock_trade = mocker.MagicMock()
        mock_trade.price = price
        
        # We assign the mock to the instance's client method
        data_instance.stock_client.get_stock_latest_trade = mocker.MagicMock(
            return_value={symbol: mock_trade}
        )

        # 2. Mock requests.get for the corporate actions API
        mock_response = {
            "corporate_actions": {
                "cash_dividends": [
                    {"symbol": symbol, "rate": 2.0},
                    {"symbol": symbol, "rate": 0.5} 
                ]
            },
            "next_page_token": None
        }

        # mocker.patch replaces 'requests.get' globally for the duration of this test
        mock_get = mocker.patch("requests.get")
        mock_get.return_value.json.return_value = mock_response
            
        data_instance.get_underlying_details([symbol])

        # 3. Assertions
        assert data_instance.asset_price_dict[symbol] == 100.0
        # Yield = (2.0 + 0.5) / 100.0 = 0.025
        assert data_instance.dividend_yield_dict[symbol] == pytest.approx(0.025)

    def test_dividend_api_pagination(self, data_instance, mocker):
        symbol = "PAGED_STOCK"
        
        # Mock price lookup
        data_instance.stock_client.get_stock_latest_trade = mocker.MagicMock(
            return_value={symbol: mocker.MagicMock(price=100.0)}
        )

        # Setup paginated responses
        resp_1 = {
            "corporate_actions": {"cash_dividends": [{"symbol": symbol, "rate": 1.0}]},
            "next_page_token": "PAGE_2"
        }
        resp_2 = {
            "corporate_actions": {"cash_dividends": [{"symbol": symbol, "rate": 1.0}]},
            "next_page_token": None
        }

        # 'side_effect' allows returning different values on consecutive calls
        mock_get = mocker.patch("requests.get")
        mock_get.return_value.json.side_effect = [resp_1, resp_2]
            
        data_instance.get_underlying_details([symbol])
            
        assert mock_get.call_count == 2
        assert data_instance.dividend_yield_dict[symbol] == pytest.approx(0.02)