import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import time
from datetime import datetime, timedelta

# Streamlit UI
#st.title("Stock Price Chart")

# Load the ticker data from the CSV file
df_tickers = pd.read_csv('tickers.csv')

# Streamlit sidebar input for selecting a company by name
selected_name = st.sidebar.selectbox('Select a company by name', df_tickers['Name'])
selected_ticker = df_tickers[df_tickers['Name'] == selected_name]['Symbol'].values[0]


# Checkbox to toggle live updates
live_updates = st.checkbox("Enable Live Updates")

if not live_updates:
    # Function to create the candlestick chart with S&P 500
    def create_candlestick_chart(selected_ticker):
        # Interval required 1 minute
        data = yf.download(tickers=selected_ticker, period='1d', interval='1m')

        # Fetch S&P 500 data
        sp500_data = yf.download('^GSPC', period='1d', interval='1m')

        # Create the candlestick trace for the selected ticker
        candlestick_trace = go.Candlestick(x=data.index,
                        open=data['Open'],
                        high=data['High'],
                        low=data['Low'],
                        close=data['Close'], name=f'{selected_ticker} data')

        # Create the S&P 500 trace on a separate Y-axis
        sp500_trace = go.Scatter(x=sp500_data.index, y=sp500_data['Close'], mode='lines', name='S&P 500', yaxis='y2')

        # Create a figure with dual Y-axes for the non-live chart
        fig = make_subplots(rows=1, cols=1, shared_xaxes=True, specs=[[{"secondary_y": True}]])
        fig.add_trace(candlestick_trace, secondary_y=False)
        fig.add_trace(sp500_trace, secondary_y=True)

        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=False)

        # Add titles
        fig.update_layout(
            yaxis_title='Stock Price (USD per Share)',
            yaxis2=dict(
                title='S&P 500',
                overlaying='y',
                side='right'
            )
        )

        # Layout for Candlestick chart
        fig.update_layout(
            autosize=True,
            width=900,
            height=600,
            xaxis_title='Date',
            yaxis_title='Price',
            xaxis_rangeslider_visible=True,
            legend=dict(
                orientation="h",  # Set the orientation to horizontal (top)
                x=0.5,  # Set the legend's x-coordinate to the center
                y=1.1,  # Set the legend's y-coordinate just above the chart
            ),
            margin=dict(
                t=10,  # Adjust the top margin value as per your preference
                l=10,
                r=10,
                b=10
            )
        )

        # X-Axes
        fig.update_xaxes(
            rangeslider_visible=True,
            rangeselector=dict(
                buttons=list([
                    dict(count=15, label="15m", step="minute", stepmode="backward"),
                    dict(count=5, label="5d", step="day", stepmode="todate"),
                    dict(count=1, label="HTD", step="hour", stepmode="todate"),
                    dict(step="all")
                ])
            ),
            #tickvals=data.index[::6],  # Show every 30 minutes
            tickformat="%H:%M",  # Format the tick labels as hour:minute
        )

        # Show the chart
        st.plotly_chart(fig)

    # Display the candlestick chart when live updates are disabled by default
    create_candlestick_chart(selected_ticker)

else:
    # Function to fetch and update stock data
    def fetch_stock_data(selected_ticker):
        selected_stock = yf.Ticker(selected_ticker)
        return selected_stock.history(period='1d', interval='1m')

    # Calculate the x-axis range for the entire trading day (from 9:30 AM to 4 PM)
    market_open_time = datetime.now().replace(hour=9, minute=00, second=0, microsecond=0)
    market_close_time = datetime.now().replace(hour=17, minute=0, second=0, microsecond=0)
    x_axis_range = [market_open_time, market_close_time]

    # Create an initial empty subplot with two Y-axes for the live chart
    fig_live = make_subplots(rows=1, cols=1, shared_xaxes=True, specs=[[{"secondary_y": True}]])
    fig_live.add_trace(go.Scatter(x=[], y=[], name=f'{selected_ticker} Price', line=dict(color='blue')), secondary_y=False)
    fig_live.add_trace(go.Scatter(x=[], y=[], name='S&P 500', line=dict(color='green')), secondary_y=True)

    # Configure the layout
    fig_live.update_xaxes(title_text='Time', range=x_axis_range)  # Set the x-axis range
    fig_live.update_yaxes(title_text=f'{selected_ticker} Price', secondary_y=False)
    fig_live.update_yaxes(title_text='S&P 500', secondary_y=True)

    # Create an empty container for the live chart
    chart_container_live = st.empty()

    # Function to create the live updating stock chart
    def create_live_stock_chart(selected_ticker):
        while live_updates:  # Keep updating while live updates are enabled
            ticker_history = fetch_stock_data(selected_ticker)

            # Update the Plotly chart with the latest data and x-axis range
            fig_live = make_subplots(rows=1, cols=1, shared_xaxes=True, specs=[[{"secondary_y": True}]])
            fig_live.add_trace(go.Scatter(x=ticker_history.index, y=ticker_history['Close'], mode='lines+markers', name=f'{selected_ticker} Price', line=dict(color='blue')), secondary_y=False)

            # Fetch S&P 500 data
            sp500_data = yf.download('^GSPC', period='1d', interval='1m')

            # Add the S&P 500 data to the live chart
            fig_live.add_trace(go.Scatter(x=sp500_data.index, y=sp500_data['Close'], mode='lines+markers', name='S&P 500', line=dict(color='green')), secondary_y=True)

            # Update the legend to be in the center and on top
            fig_live.update_layout(
                legend=dict(
                    orientation="h",  # Set the orientation to horizontal (top)
                    x=0.5,  # Set the legend's x-coordinate to the center
                    y=1.2,  # Set the legend's y-coordinate just above the chart
                )
            )

            fig_live.update_xaxes(title_text='Time', range=x_axis_range)  # Set the x-axis range
            fig_live.update_yaxes(title_text=f'{selected_ticker} Price', secondary_y=False)
            fig_live.update_yaxes(title_text='S&P 500', secondary_y=True)

            # Reduce line and marker thickness
            fig_live.update_traces(
                line=dict(width=1),  # Adjust line thickness
                marker=dict(size=3), # Adjust marker size
            )

            fig_live.update_xaxes(showgrid=False)
            fig_live.update_yaxes(showgrid=False)

            # Update the chart in the Streamlit app
            chart_container_live.plotly_chart(fig_live)

            # Sleep for 10 seconds before fetching new data
            time.sleep(10)

    # Display the live updating chart when the checkbox is selected
    create_live_stock_chart(selected_ticker)
    if st.button("Stop"):
        st.warning("Live updates are enabled! Please turn it off before pressing stop.")
