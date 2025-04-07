import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))  
parent_dir = os.path.dirname(current_dir)  
realized_vol_path = os.path.join(parent_dir, 'realized_vol')
print(realized_vol_path)
sys.path.append(realized_vol_path)
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from realized_vol.data_loader import MarketDataLoader
from realized_vol.vol_engine import RealizedVolEngine

import streamlit as st
st.write("Volatility Engine imported successfully!")

@st.cache_data
def fetch_data(tickers, start_date, end_date):
    loader = MarketDataLoader(tickers=tickers, start=start_date, end=end_date)
    price_data = loader.fetch_price_series()
    return price_data

def highlight_spikes(vol_data, threshold_factor=2):
    avg_vol = vol_data.rolling(window=21).mean()
    spike_threshold = avg_vol * threshold_factor
    spikes = vol_data[vol_data > spike_threshold]
    return spikes

st.title("Volatility Dashboard")

ticker = st.sidebar.text_input("Enter Ticker:", "AAPL")
start_date = st.sidebar.date_input("Start Date:", pd.to_datetime("2020-01-01"))
end_date = st.sidebar.date_input("End Date:", pd.to_datetime("2025-04-07"))
vol_type = st.sidebar.selectbox("Select Vol Type", ["Simple Realized VOL", "Parkinson VOL", "Garman-Klass VOL", "Hodges-Tompkins VOL"])
spike_threshold = st.sidebar.number_input("Set Spike Threshold", min_value=0.0, max_value=2.0, value=2.0,  step=0.1)

price_data = fetch_data([ticker], str(start_date), str(end_date))
engine = RealizedVolEngine(price_series=price_data)
vol_data = None

if vol_type == "Simple Realized VOL":
    vol_data = engine.compute_realized_vol()
elif vol_type == "Parkinson VOL":
    vol_data = engine.compute_parkinson_vol()
elif vol_type == "Garman-Klass VOL":
    vol_data = engine.compute_garman_klass_vol()
elif vol_type == "Hodges-Tompkins VOL":
    vol_data = engine.compute_hodges_tomkins_vol()

spikes = highlight_spikes(vol_data=vol_data, threshold_factor=float(spike_threshold))

st.subheader(f"Volatility Analysis for {ticker}")
fig, ax = plt.subplots(figsize=(10, 6))

ax.plot(vol_data, label=f"{vol_type} - {ticker}")
ax.scatter(spikes.index, spikes, color="red", label="Volatility Spikes", zorder=5)

ax.set_title(f"{vol_type} for {ticker}")
ax.set_xlabel("Date")
ax.set_ylabel("Volatility")
ax.legend()

st.pyplot(fig)

mean_volatility = vol_data.mean()  
if isinstance(mean_volatility, pd.Series):
    mean_volatility = mean_volatility.values[0]
st.subheader("Statistics")
st.write(f"Average Volatility: {mean_volatility:.4f}")
st.write(f"Volatility Spikes (above threshold): {len(spikes)}")