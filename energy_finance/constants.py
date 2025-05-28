from enum import Enum

SUPPORTED_NAMES = [
    "gold",
    "platinum",
    "lean_hogs",
    "oat",
    "aluminum",
    "soybean_meal",
    "lumber",
    "micro_gold",
    "feeder_cattle",
    "rough_rice",
    "palladium"
]


class DataSource(Enum):
    FMP = "fmp"
    COMMODITYPRICEAPI = 'commodity_price_api'
    API_NINJAS = "api_ninjas"
    ALPHA_VANTAGE = "alpha_vantage"