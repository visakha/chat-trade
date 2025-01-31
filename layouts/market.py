import dash
from dash import html

def create_market_layout():
    """Create the market overview layout"""
    return html.Div(
        [
            html.H3("Market Overview"),
            html.P("Market overview features coming soon..."),
        ],
        className="content"
    )

market_layout = create_market_layout()
