# Volatility (VOL) - Core concepts:

## What is Volatility?
* Measure of dispersion of returns for a given security
* Measure of how much the price of a security moves over time

### Types:
- Realized/Historical VOL : 
    - What has happened in the past, historical prices, risk analysis, backtesting, stress testing
- Implied VOL:
    - What market expects in the future, option prices, forward looking risks, option pricing, strategy

## Realized Volatility:
**Annualized Standard Deviation of Log Returns**
Steps:
- Get daily prices -> Compute log returns:
$$ r_t = ln(\frac{p_t}{p_{t-1}})$$
- Compute std deviation of returns over a window (eg. 21 days for month)
- Annualize it:
$$ \sigma = std(r) \times \sqrt{N}$$
where $N = 252$ trading days in a year (or adjusted for any frequency)

### Types of Realized VOL:
- Simple StdDev VOL: most common $\rightarrow$ `returns.rolling(window).std() * sqrt(252)`
- Exponentially weighted VOL: gives more weight to recent moves $\rightarrow$ `pandas.ewm(span).std()`
- Parkinson/Garman-Klass VOL: uses high/low/open/close (more precise) $\rightarrow$ `arch` or `volatility` python libs

## Implied Volatility 
**Reverse-engineer VOL from option prices using Black-Scholes or other models**

Option prices = function(spot price, strike price, time to expiry, risk-free rate, volatility) $\rightarrow$ input price $\rightarrow$ solve for VOL

### Black-Scholes inputs:
- Spot Price (S)
- Strike Price (K)
- Time to Expiry (T)
- Risk-free Rate (r)
- Implied VOL ($\sigma$) $\leftarrow$ what we want

### In practice:
- scipy.optimize to iteratively solve for VOL
- py-vollib or QuantLib

### Term structure of IV:
Markets price different IV for different expiries:
- 1 week: High VOL (event risk like earnings)
- 1 month: Medium 
- 3+ months: Lower (averaging effects)

#### Skew of IV:
Marktets price different IV for different strikes:
- Far OTM puts $\rightarrow$ Very High (crash protection premium)
- ATM options $\rightarrow$ Baseline IV
- Far OTM calls $\rightarrow$ Lower IV

This _skew_ tells a story of market fear or greed.


## Project ladder:
1. Realized VOL engine $\rightarrow$ Compute VOL across tickers, sectors, countries etc
2. IV fetcher/calculator $\rightarrow$ Pull IV from API (like Tradier, Polygon, Yahoo options) or calculate it
3. Compare Realized vs Implied VOL $\rightarrow$ VOL Arbitrage detection, skew analysis, anomaly detection
4. VOL surface visualizer $\rightarrow$ Heatmap of VOL vs strike vs expiry
5. VOL forecasting model $\rightarrow$ Predict future realized VOL based on current IV, macro, news


