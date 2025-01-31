import dash
from dash import html, dcc

def create_sidebar():
    """Create the sidebar layout for the application"""
    return html.Div(
        [
            html.Div(
                [
                    html.H2("Stock Insights", className="app-title"),
                    html.Hr(),
                    dcc.Link('Technical Analysis', href='/', className='nav-link'),
                    html.Br(),
                    dcc.Link('Portfolio', href='/portfolio', className='nav-link'),
                    html.Br(),
                    dcc.Link('Market Overview', href='/market', className='nav-link'),
                ],
                className="sidebar-content"
            ),
        ],
        className="sidebar",
    )

sidebar = create_sidebar()
