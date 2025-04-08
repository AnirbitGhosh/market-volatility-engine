import dash
from dash import dcc, html, Input, Output, State, callback_context
import plotly.graph_objs as go
import pandas as pd
from realized_vol.data_loader import MarketDataLoader
from realized_vol.vol_engine import RealizedVolEngine
from utils import detect_spikes
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta
import traceback
from io import StringIO

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LUX])
server = app.server

loader = MarketDataLoader()

default_end = datetime.now()
default_start = default_end - timedelta(days=3*365)

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Market Volatility Dashboard", className="text-center my-4"), width=12)
    ]),

    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Controls", className="card-title"),
                    dbc.InputGroup([
                        dbc.Input(
                            id='ticker-input',
                            placeholder='Enter Ticker(s) separated by comma',
                            value='AAPL,MSFT,GOOG'
                        ),
                        dbc.Button('Load Data', id='load-button', color="primary"),
                    ], className="mb-3"),
                    
                    dbc.Row([
                        dbc.Col([
                            html.Label("Date Range Start"),
                            dcc.DatePickerSingle(
                                id='start-date',
                                min_date_allowed='2000-01-01',
                                max_date_allowed=default_end,
                                initial_visible_month=default_start,
                                date=default_start.strftime('%Y-%m-%d'),
                                className="mb-3"
                            )
                        ]),
                        dbc.Col([
                            html.Label("Date Range End"),
                            dcc.DatePickerSingle(
                                id='end-date',
                                min_date_allowed='2000-01-01',
                                max_date_allowed=default_end,
                                initial_visible_month=default_end,
                                date=default_end.strftime('%Y-%m-%d'),
                                className="mb-3"
                            )
                        ])
                    ]),
                    
                    html.Label("Volatility Window (days)"),
                    dcc.Slider(
                        id='vol-window',
                        min=5,
                        max=60,
                        step=5,
                        value=21,
                        marks={i: str(i) for i in range(5, 61, 5)},
                        className="mb-3"
                    ),
                    
                    html.Label("Spike Detection Threshold"),
                    dcc.Slider(
                        id='spike-threshold',
                        min=1.0,
                        max=4.0,
                        step=0.1,
                        value=2.5,
                        marks={i: f"{i}σ" for i in [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]},
                        className="mb-3"
                    ),
                    
                    html.Label("Volatility Types to Display"),
                    dbc.Checklist(
                        id='vol-types',
                        options=[
                            {'label': ' Realized VOL', 'value': 'Realized VOL'},
                            {'label': ' Parkinson VOL', 'value': 'Parkinson VOL'},
                            {'label': ' Garman-Klass VOL', 'value': 'Garman-Klass VOL'},
                            {'label': ' Hodges-Tompkins VOL', 'value': 'Hodges-Tompkins VOL'},
                        ],
                        value=['Realized VOL', 'Parkinson VOL'],
                        inline=True,
                        switch=True,
                        className="mb-3"
                    ),
                    
                    dbc.Button("S&P 500 List", id="sp500-button", color="info", className="mt-2")
                ])
            ])
        ], md=3),
        
        dbc.Col([
            dbc.Spinner(
                html.Div(id='plots-container'),
                color="primary",
                spinner_style={"width": "3rem", "height": "3rem"}
            ),
            dcc.Store(id='data-store')  
        ], md=9)
    ]),
    
    dbc.Modal([
        dbc.ModalHeader("S&P 500 Constituents"),
        dbc.ModalBody(id="sp500-modal-body"),
        dbc.ModalFooter(
            dbc.Button("Close", id="close-sp500-modal", className="ml-auto")
        ),
    ], id="sp500-modal", size="lg"),
    
    dcc.Interval(id='interval-component', interval=60*60*1000, n_intervals=0)  # Hourly refresh
], fluid=True)

@app.callback(
    Output('data-store', 'data'),
    [Input('load-button', 'n_clicks'),
     Input('interval-component', 'n_intervals')],
    [State('ticker-input', 'value'),
     State('start-date', 'date'),
     State('end-date', 'date')]
)
def load_and_store_data(n_clicks, n_intervals, tickers, start_date, end_date):
    if not tickers:
        return dash.no_update
    
    tickers = [ticker.strip().upper() for ticker in tickers.split(',')]
    loader.set_tickers(tickers)
    
    try:
        df = loader.fetch_price_series(tuple(tickers), start_date, end_date)
        return df.to_json(date_format='iso', orient='split')
    except Exception as e:
        return dash.no_update

@app.callback(
    Output('plots-container', 'children'),
    [Input('data-store', 'data'),
     Input('vol-types', 'value'),
     Input('vol-window', 'value'),
     Input('spike-threshold', 'value')]
)
def update_plots(json_data, selected_vols, window, threshold):
    if json_data is None:
        return dbc.Alert("Please enter tickers and click 'Load Data'", color="info")
    
    try:
        # Read JSON data with StringIO
        df = pd.read_json(StringIO(json_data), orient='split')
        
        print("\nRaw DataFrame Structure:")
        print("Columns:", df.columns)
        print("Shape:", df.shape)
        
        # Extract unique tickers from the MultiIndex columns
        if isinstance(df.columns, pd.MultiIndex):
            tickers = list(df.columns.levels[1].unique())
        else:
            # Handle case where columns are tuples but not proper MultiIndex
            tickers = list(set(col[1] for col in df.columns if isinstance(col, tuple)))
        
        print(f"\nProcessing {len(tickers)} tickers:", tickers)
        
        graphs = []
        
        for ticker in tickers:
            try:
                print(f"\nProcessing ticker: {ticker}")
                
                # Select columns for this ticker - works for both MultiIndex and tuple columns
                col_mask = [col[1] == ticker for col in df.columns]
                prices = df.loc[:, col_mask].copy()
                
                # Rename columns to remove ticker suffix
                prices.columns = [col[0] for col in prices.columns]
                print("Prices columns after selection:", prices.columns)
                
                # Get close prices
                price_data = prices['Close']
                print("Price data sample:", price_data.head(2))
                
                # Calculate volatilities
                engine = RealizedVolEngine(prices, window=window)
                vols = engine.calculate_all_volatility_types()
                print("Volatilities calculated:", list(vols.columns))
                
                # Create price trace
                traces = [
                    go.Scatter(
                        x=vols.index,
                        y=price_data,
                        name=f"{ticker} Price",
                        yaxis='y2',
                        line=dict(color='#2c3e50', width=1.5),
                        opacity=0.8,
                        hovertemplate="Price: %{y:.2f}<extra></extra>"
                    )
                ]
                
                # Add volatility traces
                vol_colors = {
                    'Realized VOL': '#e74c3c',
                    'Parkinson VOL': '#3498db',
                    'Garman-Klass VOL': '#2ecc71',
                    'Hodges-Tompkins VOL': '#9b59b6'
                }
                
                for vol_type in selected_vols:
                    if vol_type in vols.columns:
                        traces.append(go.Scatter(
                            x=vols.index,
                            y=vols[vol_type],
                            name=f"{ticker} {vol_type}",
                            line=dict(color=vol_colors.get(vol_type, '#34495e'), width=2),
                            opacity=0.9,
                            hovertemplate=f"{vol_type}: %{{y:.2f}}<extra></extra>"
                        ))
                
                # Create figure
                fig = go.Figure(
                    data=traces,
                    layout=go.Layout(
                        title=f'{ticker} Volatility Analysis',
                        xaxis=dict(
                            rangeslider=dict(visible=True),
                            type='date'
                        ),
                        yaxis=dict(title='Volatility'),
                        yaxis2=dict(
                            title='Price',
                            overlaying='y',
                            side='right',
                            showgrid=False
                        ),
                        hovermode='x unified',
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1
                        )
                    )
                )
                
                # Add time range buttons
                fig.update_xaxes(
                    rangeselector=dict(
                        buttons=list([
                            dict(count=1, label="1m", step="month", stepmode="backward"),
                            dict(count=6, label="6m", step="month", stepmode="backward"),
                            dict(count=1, label="YTD", step="year", stepmode="todate"),
                            dict(count=1, label="1y", step="year", stepmode="backward"),
                            dict(step="all")
                        ])
                    )
                )
                
                graphs.append(dbc.Card(
                    dbc.CardBody(dcc.Graph(figure=fig)),
                    className="mb-4"
                ))
                
            except Exception as e:
                error_msg = f"Error processing {ticker}: {str(e)}"
                print(error_msg)
                graphs.append(dbc.Alert(error_msg, color="warning"))
        
        return graphs if graphs else dbc.Alert("No data to display", color="info")
    
    except Exception as e:
        error_msg = f"Initial processing error: {str(e)}"
        print(error_msg)
        return dbc.Alert(error_msg, color="danger")

@app.callback(
    Output("sp500-modal", "is_open"),
    [Input("sp500-button", "n_clicks"), 
     Input("close-sp500-modal", "n_clicks")],
    [State("sp500-modal", "is_open")],
)
def toggle_sp500_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@app.callback(
    Output("sp500-modal-body", "children"),
    [Input("sp500-button", "n_clicks")]
)
def update_sp500_modal(n):
    if n is None:
        return dash.no_update
    
    try:
        tickers = loader.get_sp500_tickers()
        cols = 4
        chunk_size = (len(tickers) + cols - 1) // cols
        ticker_chunks = [tickers[i:i + chunk_size] for i in range(0, len(tickers), chunk_size)]
        
        return dbc.Row([
            dbc.Col([
                html.Ul([html.Li(ticker) for ticker in chunk], className="list-unstyled")
            ]) for chunk in ticker_chunks
        ])
    except Exception as e:
        return dbc.Alert(f"Failed to load S&P 500 list: {str(e)}", color="danger")

if __name__ == "__main__":
    app.run(debug=True)