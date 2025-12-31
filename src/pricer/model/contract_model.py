from dataclasses import dataclass
import datetime
import pandas as pd
import alpaca
from alpaca.trading.enums import AssetStatus, ContractType, ExerciseStyle
# https://alpaca.markets/sdks/python/api_reference/trading/models.html#optioncontract
@dataclass
class ContractModel:
  close_price: float
  id: str
  symbol: str
  name: str
  expiration_date: datetime
  underlying_symbol: str
  type: str
  style: str
  strike_price: float
  open_interest: int
  size: int

  @staticmethod
  def from_class(var: alpaca.trading.models.OptionContract) -> pd.DataFrame:
    return ContractModel(
        close_price=float(var.close_price),
        id=var.id,
        symbol=var.symbol,
        name=var.name,
        expiration_date=var.expiration_date,
        underlying_symbol=var.underlying_symbol,
        type="call" if var.type == ContractType.CALL else "put",
        style="european" if var.style == ExerciseStyle.EUROPEAN else "american" if var.style == ExerciseStyle.AMERICAN else "others",
        strike_price=float(var.strike_price),
        open_interest=int(var.open_interest),
        size=int(var.size)
        )