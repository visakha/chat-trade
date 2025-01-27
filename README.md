# Stock Technical Analysis Dash App

## Overview
This Dash application provides interactive technical analysis for stocks, featuring multiple technical indicators and interactive charting.

## Setup Instructions
1. Clone the repository
2. Create a virtual environment:
   ```
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Run the application:
   ```
   python app.py
   ```

5. All in one
   ```
   cd /Users/konark/CascadeProjects/windsurf-project
&& python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
&& python app.py
   ```

 6. Kill the app : 8050 is the port
   ```
   lsof -i :8050 | grep Python | awk '{print $2}' | xargs kill -9
   ```  


## Features
- Real-time stock price retrieval
- Multiple technical indicators
- Interactive Plotly chart
- Responsive Dash interface

## Technical Indicators
- Moving Averages (SMA, EMA)
- Relative Strength Index (RSI)
- Bollinger Bands
- MACD
- Stochastic Oscillator
