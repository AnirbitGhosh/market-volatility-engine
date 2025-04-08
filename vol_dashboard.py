import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objs as go
import pandas as pd
from realized_vol.data_loader import MarketDataLoader
from realized_vol.vol_engine import RealizedVolEngine
from utils import detect_spikes

app = dash.Dash(__name__)
server = app.server

loader = MarketDataLoader()

app.layout = html.Div([
    html.H1("Realized Volatility Engine"),

    dcc.Input(id='ticker-input', type='text', placeholder='Enter Ticker(s) seprated by comma'),
    html.Button('Load Data', id='load-button', n_clicks=0),

    dcc.Checklist(
        id='vol-types',
        options=[{'label': v, 'value': v} for v in ['Realized VOL', 'Parkinson VOL', 'Garman-Klass VOL', 'Hodges-Tompkins VOL']],
        value=['Realized VOL', 'Parkinson VOL', 'Garman-Klass VOL', 'Hodges-Tompkins VOL'],
        labelStyle={'display': 'inline-block'}
    ),

    html.Div(id='plots-container')
])

@app.callback(
    Output('plots-container', 'children'),
    Input('load-button', 'n_clicks'),
    State('ticker-input', 'value'),
    State('vol-types', 'value')
)
def update_graph(n_clicks, tickers, selected_vols):
    if n_clicks == 0 or not tickers:
        return []
    
    tickers = [ticker.strip().upper() for ticker in tickers.split(',')]
    loader.set_tickers(tickers)
    df = loader.fetch_price_series()

    graphs = []

    for ticker in tickers:
        price_data = df['Close'][ticker] if len(tickers) > 1 else df['Close']
        prices = df.xs(ticker, axis=1, level=1, drop_level=False) if len(tickers) > 1 else df

        engine = RealizedVolEngine(prices)

        vols = engine.calculate_all_volatility_types()
        crosshair_time = vols.index

        traces = [go.Scatter(x=crosshair_time, y=price_data, name=f"{ticker} Price", yaxis='y2')]

        for vol_type in selected_vols:
            traces.append(go.Scatter(x=crosshair_time, y=vols[vol_type], name=f"{ticker} - { vol_type}"))

        annotations = detect_spikes(vols['Realized VOL'])

        layout = go.Layout(
            title=f'{ticker} Volatility & Price',
            xaxis=dict(showspikes=True, spikemode='across', spikesnap='cursor', showline=True),
            yaxis=dict(title='Volatility'),
            yaxis2=dict(title='Price', overlaying='y', side='right'),
            hovermode='x unified',
            annotations=annotations
        )

        fig = go.Figure(data=traces, layout=layout)
        graphs.append(dcc.Graph(figure=fig))

    return graphs

if __name__ == "__main__":
    app.run(debug=True)