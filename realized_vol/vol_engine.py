import sys
import numpy as np
import pandas as pd
from realized_vol.config import TRADING_DAYS_PER_YEAR

class RealizedVolEngine:
    def __init__(self, price_series: pd.DataFrame, window: int = 21, annualized: bool = True):
        self.price_series = price_series
        self.window = window
        self.annualized = annualized

    def compute_realized_vol(self) -> pd.Series:
        returns = (self.price_series['Close'] / self.price_series['Close'].shift(1)).apply(np.log)
        vol = returns.rolling(window=self.window).std()

        if self.annualized:
            vol *= np.sqrt(TRADING_DAYS_PER_YEAR)
        
        return vol
    
    def compute_parkinson_vol(self) -> pd.Series:
        park_vol = (1.0 / (4.0 * np.log(2.0))) * (
            (self.price_series['High'] / self.price_series['Low']).apply(np.log)
         ) ** 2.0 
        
        def f(v):
            return (TRADING_DAYS_PER_YEAR * v.mean()) ** 0.5
        
        result = park_vol.rolling(window=self.window).apply(func=f)

        return result
    
    def compute_garman_klass_vol(self) -> pd.Series:
        log_hl = (self.price_series['High'] / self.price_series['Low']).apply(np.log)
        log_co = (self.price_series['Close'] / self.price_series['Open']).apply(np.log)

        gk_vol = 0.5 * log_hl ** 2 - (2 * np.log(2) - 1) * log_co ** 2

        def f(v):
            return (TRADING_DAYS_PER_YEAR * v.mean()) ** 0.5
        
        result = gk_vol.rolling(window=self.window).apply(func=f)
        
        return result
    
    def compute_hodges_tomkins_vol(self) -> pd.Series:
        log_return = (self.price_series['Close'] / self.price_series['Close'].shift(1)).apply(np.log)

        ht_vol = log_return.rolling(window=self.window).std() * np.sqrt(TRADING_DAYS_PER_YEAR)

        h = self.window
        n = (log_return.count() - h) + 1

        adj_factor = 1.0 / (1.0 - (h / n) + ((h**2 - 1) / (3 * n ** 2)))

        result = ht_vol * adj_factor

        return result
    
    def calculate_all_volatility_types(self) -> pd.Series:
        realized_vol = self.compute_realized_vol()
        park_vol = self.compute_parkinson_vol()
        gk_vol = self.compute_garman_klass_vol()
        ewma_vol = self.compute_ewma_vol()

        vol_df = pd.DataFrame({
            'Realized VOL': realized_vol,
            'Parkinson VOL': park_vol,
            'Garman-Klass VOL': gk_vol,
            'EWMA VOL': ewma_vol
        })

        return vol_df
