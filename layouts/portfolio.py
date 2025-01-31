import dash
from dash import html

def create_portfolio_layout():
    """Create the portfolio analysis layout"""
    return html.Div(
        [
            html.H3("Portfolio Analysis"),
            html.P("Portfolio analysis features coming soon..."),
        ],
        className="content"
    )

portfolio_layout = create_portfolio_layout()
