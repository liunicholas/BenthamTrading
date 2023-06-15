from twelvedata import TDClient
# import requests
import trading_clock as tc
import silver_bullet as sb
from polygon import RESTClient

# alpha_vantage_api_key = "IU7OJ3GBEV5SBQOX"
polygon_api_key = "jyDl3qsKZLKRg51FuqC5ucPBFLMGO3cL"
twelvedata_api_key = '118aed5a291f4a9fb7c36cfb590db853'

### Alpha Vantage 
# url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=SPY&interval={tc.INTERVAL}min&apikey={alpha_vantage_api_key}"

# r = requests.get(url)
# data = r.json()
# print(data)

### Polygon 
# client = RESTClient(api_key=polygon_api_key)
# ticker = "spx"

# List Aggregates (Bars)
# bars = client.get_aggs(ticker=ticker, multiplier=1,
#                        timespan="day", from_="2023-06-13", to="2023-06-14")
# for bar in bars:
#     print(bar)

# Twelve data
td = TDClient(apikey=twelvedata_api_key)
ts = td.time_series(
    symbol="gspc",
    interval=f"{sb.INTERVAL}min",
    timezone=tc.new_york_tz,
    start_date="2023-06-13",
    end_date="2023-06-14",
).as_pandas()

print(ts.head())
