import yfinance as yf
import pandas as pd
import requests

class MarketDataLoader:
    def __init__(self, tickers: list=None, start: str = "2020-01-01", end: str = "2025-04-07"):
        self.tickers = tickers
        self.start = start
        self.end = end
    
    def fetch_price_series(self) -> pd.Series:
        df = yf.download(self.tickers, start=self.start, end=self.end, progress=False)
        if df.empty:
            raise ValueError("Data Not Fetched - check Ticker or date range")
        
        return df
    
    def get_sp500_tickers(self) -> list:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        tables = pd.read_html(url)
        sp500_table = tables[0]
        tickers = sp500_table['Symbol'].tolist()
        return tickers
    
    def set_tickers(self, tickers: list): 
        self.tickers = tickers