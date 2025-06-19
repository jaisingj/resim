import pandas as pd
import requests

def fetch_stock_history_fmp(ticker, start_date, end_date):
    url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}?from={start_date}&to={end_date}&apikey=YOUR_FMP_KEY"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if "historical" in data:
            df = pd.DataFrame(data["historical"])
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            df.sort_index(inplace=True)
            return df
    return pd.DataFrame()
