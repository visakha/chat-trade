import dash
from dash import html, dcc
import pandas as pd

def create_technical_analysis_layout():
    """Create the technical analysis layout"""
    return html.Div(
        [
            html.Div(
                [
                    html.H3("Stock Technical Analysis", style={'margin-bottom': '20px'}),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Label("Stock Symbol:", className="control-label"),
                                    dcc.Input(
                                        id='symbol-input',
                                        value='AAPL',
                                        type='text',
                                        className="input-field"
                                    ),
                                ],
                                className="control-group"
                            ),
                            html.Div(
                                [
                                    html.Label("Date Range:", className="control-label"),
                                    dcc.DatePickerRange(
                                        id='date-range',
                                        min_date_allowed=pd.Timestamp.now().date() - pd.Timedelta(days=365*2),
                                        max_date_allowed=pd.Timestamp.now().date(),
                                        start_date=pd.Timestamp.now().date() - pd.Timedelta(days=365),
                                        end_date=pd.Timestamp.now().date(),
                                        className="date-picker"
                                    ),
                                ],
                                className="control-group"
                            ),
                            html.Div(
                                [
                                    html.Label("Technical Indicators:", className="control-label"),
                                    dcc.Checklist(
                                        id='indicators-checklist',
                                        options=[
                                            {'label': 'SMA 50', 'value': 'sma50'},
                                            {'label': 'SMA 200', 'value': 'sma200'},
                                            {'label': 'EMA 50', 'value': 'ema50'},
                                            {'label': 'EMA 200', 'value': 'ema200'},
                                            {'label': 'RSI', 'value': 'rsi'},
                                            {'label': 'MACD', 'value': 'macd'},
                                            {'label': 'Bollinger Bands', 'value': 'bbands'},
                                            {'label': 'VWAP', 'value': 'vwap'}
                                        ],
                                        value=['sma50', 'sma200'],
                                        className="checklist-container"
                                    ),
                                ],
                                className="control-group"
                            ),
                        ],
                        className="controls-container"
                    ),
                    html.Div(
                        dcc.Graph(id='stock-chart'),
                        className="chart-container"
                    ),
                ],
                className="content"
            ),
        ],
        className="main-content"
    )

technical_analysis_layout = create_technical_analysis_layout()
