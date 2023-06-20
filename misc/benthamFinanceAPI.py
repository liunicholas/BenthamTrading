import requests
from twelvedata import TDClient
# import requests
import sys
sys.path.insert(1, '..')
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
    symbol="ESU3",
    interval=f"{sb.INTERVAL}min",
    timezone=tc.new_york_tz,
    start_date="2023-06-16",
    end_date="2023-06-17",
).as_pandas()

print(ts.head())


# Function to get the symbol for E-mini S&P 500 futures
# def get_emini_symbol():
#     url = f'https://api.twelvedata.com/symbol_search?symbol=E-mini%20S%26P%20500%20Futures&exchange=CME&apikey={twelvedata_api_key}'

#     try:
#         response = requests.get(url)
#         data = response.json()
#         if 'data' in data and data['data']:
#             symbol = data['data'][0]['symbol']
#             return symbol
#         else:
#             print('Error: Unable to fetch E-mini S&P 500 futures symbol.')
#             return None
#     except requests.exceptions.RequestException as e:
#         print('Error: ', e)
#         return None


# # Get the symbol for E-mini S&P 500 futures
# emini_symbol = get_emini_symbol()

# if emini_symbol is not None:
#     print(f"The symbol for E-mini S&P 500 futures is {emini_symbol}")
