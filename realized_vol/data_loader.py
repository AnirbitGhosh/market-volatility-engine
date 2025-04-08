import yfinance as yf
import pandas as pd
import requests
from datetime import datetime
from functools import lru_cache
import hashlib

class MarketDataLoader:
    def __init__(self, tickers: list=None, start: str = "2020-01-01", end: str = None):
        self.tickers = tickers
        self.start = start
        self.end = end or datetime.now().strftime('%Y-%m-%d')
        self._current_cache_keys = set()

    def _generate_cache_key(self, tickers: tuple, start: str, end: str) -> str:
        key_str = f"{tickers}_{start}_{end}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    @lru_cache(maxsize=32)
    def _cached_fetch(self, cache_key: str, tickers: tuple, start: str, end: str) -> pd.DataFrame:
        ticker_list = list(tickers) if isinstance(tickers, tuple) else tickers
        df = yf.download(ticker_list, start=start, end=end, progress=False)
        if df.empty:
            raise ValueError("Data Not Fetched - check Ticker or date range")
        
        df = df.ffill().bfill()
        return df
    
    def fetch_price_series(self, tickers: tuple, start: str, end: str) -> pd.DataFrame:
        cache_key = self._generate_cache_key(tickers, start, end)

        self._current_cache_keys.add(cache_key)

        if len(self._current_cache_keys) > 32:
            oldest_key = next(iter(self._current_cache_keys))
            self._cached_fetch.cache_clear()
            self._current_cache_keys = set()
            print(f"Cleared cache due to size limit (was {len(self._current_cache_keys)} items)")

        return self._cached_fetch(cache_key, tickers, start, end)
    
    def clear_cache(self):
        self._cached_fetch.cache_clear()
        self._current_cache_keys = set()
        print("Cache cleared")
    
    @lru_cache(maxsize=1)  
    def get_sp500_tickers(self) -> list:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        tables = pd.read_html(url)
        sp500_table = tables[0]
        tickers = sp500_table['Symbol'].tolist()
        return tickers
    
    def set_tickers(self, tickers: list): 
        self.tickers = tickers