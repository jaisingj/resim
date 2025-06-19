import pandas as pd
from imports import *
from pandas.tseries.offsets import BDay
from app import get_news_yahoo, score_news, color_cells
from nltk.sentiment.vader import SentimentIntensityAnalyzer

def analyze_stock():
    # Load ticker symbols from CSV
    df_tickers = pd.read_csv('tickers.csv')
    options = df_tickers['Name'].tolist()

    # Sidebar with dropdown select input and start date input
    selected_name = st.sidebar.selectbox('Select a stock', options)
    start_date = st.sidebar.date_input('Start Date', value=dt.datetime(2019, 1, 1))

    # Get the selected ticker directly from the user selection
    selected_ticker = df_tickers[df_tickers['Name'] == selected_name]['Symbol'].values[0]

    # Assign selected_ticker to session state
    st.session_state.selected_ticker = selected_ticker

    # Retrieve stock data using yfinance
    start = dt.datetime(start_date.year, start_date.month, start_date.day)
    data = yf.download(selected_ticker, start=start)

    # Calculate 10-day and 20-day moving averages
    data['10_MA'] = data['Close'].rolling(window=10).mean()
    data['20_MA'] = data['Close'].rolling(window=20).mean()

    # Remove the volume from the table
    data_table = data.drop('Volume', axis=1)

    # Remove the timestamp from the index
    data_table.index = data_table.index.normalize()

    # Calculate buy and sell signals
    Trade_Buy = []
    Trade_Sell = []

    for i in range(len(data) - 1):
        if ((data['10_MA'].values[i] < data['20_MA'].values[i]) and (data['10_MA'].values[i+1] > data['20_MA'].values[i+1])):
            Trade_Buy.append(data_table.index[i])
        elif ((data['10_MA'].values[i] > data['20_MA'].values[i]) and (data['10_MA'].values[i+1] < data['20_MA'].values[i+1])):
            Trade_Sell.append(data_table.index[i])

    # Create a combined line chart with moving averages using Plotly
    # Full data plot
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=data_table.index, y=data_table['Close'], mode='lines', name='Closing Price'))
    fig1.add_trace(go.Scatter(x=data_table.index, y=data_table['10_MA'], mode='lines', name='10-day MA'))
    fig1.add_trace(go.Scatter(x=data_table.index, y=data_table['20_MA'], mode='lines', name='20-day MA'))
    fig1.add_trace(go.Scatter(x=Trade_Buy, y=data_table.loc[Trade_Buy, 'Close'], mode='markers', name='Buy Signal', marker=dict(color='green', size=8)))
    fig1.add_trace(go.Scatter(x=Trade_Sell, y=data_table.loc[Trade_Sell, 'Close'], mode='markers', name='Sell Signal', marker=dict(color='red', size=8)))
    fig1.update_layout(
        title='Price Trend', xaxis_title='Date', yaxis_title='Price',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),  # Adjust both y and x anchor positions
        margin=dict(l=50, r=50, t=90, b=40),  # Adjust the margin values as needed
        height=600  # Adjust the height of the plot as needed
    )

    # Zoomed data plot
    # Define last_180_days
    last_90_days = data_table.index[-90:]

    # Convert last_90_days to pandas DatetimeIndex
    last_90_days = pd.DatetimeIndex(last_90_days)

    # Convert lists to pandas DatetimeIndex
    Trade_Buy_Dates = pd.DatetimeIndex(Trade_Buy)
    Trade_Sell_Dates = pd.DatetimeIndex(Trade_Sell)

    # Get buy and sell signals for last 90 days
    last_90_Trade_Buy = Trade_Buy_Dates[Trade_Buy_Dates >= last_90_days[0]].tolist()
    last_90_Trade_Sell = Trade_Sell_Dates[Trade_Sell_Dates >= last_90_days[0]].tolist()

    # Create a new figure
    fig2 = go.Figure()

    fig2.add_trace(go.Scatter(x=last_90_days, y=data_table['Close'].loc[last_90_days], mode='lines', name='Closing Price'))
    fig2.add_trace(go.Scatter(x=last_90_days, y=data_table['10_MA'].loc[last_90_days], mode='lines', name='10-day MA'))
    fig2.add_trace(go.Scatter(x=last_90_days, y=data_table['20_MA'].loc[last_90_days], mode='lines', name='20-day MA'))
    fig2.add_trace(go.Scatter(x=last_90_Trade_Buy, y=data_table.loc[last_90_Trade_Buy, 'Close'],
                              mode='markers', name='Buy Signal', marker=dict(color='green', size=8)))
    fig2.add_trace(go.Scatter(x=last_90_Trade_Sell, y=data_table.loc[last_90_Trade_Sell, 'Close'],
                              mode='markers', name='Sell Signal', marker=dict(color='red', size=8)))
    fig2.update_layout(title='Last 6-Mths Trend', xaxis_title='Date', yaxis_title='Price',
                       legend=dict(orientation="h", y=1.02, x=0.5))  # Move the legend to the bottom

    # Create a table with buy and sell signals
    data_table_with_signals = data_table.copy()
    data_table_with_signals['Signal'] = ''

    # Format the relevant columns to two decimal places
    data_table_with_signals['Open'] = data_table_with_signals['Open'].apply(lambda x: '{:.2f}'.format(x))
    data_table_with_signals['High'] = data_table_with_signals['High'].apply(lambda x: '{:.2f}'.format(x))
    data_table_with_signals['Low'] = data_table_with_signals['Low'].apply(lambda x: '{:.2f}'.format(x))
    data_table_with_signals['Close'] = data_table_with_signals['Close'].apply(lambda x: '{:.2f}'.format(x))
    data_table_with_signals['Adj Close'] = data_table_with_signals['Adj Close'].apply(lambda x: '{:.2f}'.format(x))
    data_table_with_signals['10_MA'] = data_table_with_signals['10_MA'].apply(lambda x: '{:.2f}'.format(x))
    data_table_with_signals['20_MA'] = data_table_with_signals['20_MA'].apply(lambda x: '{:.2f}'.format(x))

    # Generate 'Signal' based on 'Buy' and 'Sell' logic
    for i in range(len(data_table_with_signals) - 1):
        if ((data_table_with_signals['10_MA'].values[i] < data_table_with_signals['20_MA'].values[i]) and (data_table_with_signals['10_MA'].values[i+1] > data_table_with_signals['20_MA'].values[i+1])):
            data_table_with_signals['Signal'].iloc[i] = 'Buy'
        elif ((data_table_with_signals['10_MA'].values[i] > data_table_with_signals['20_MA'].values[i]) and (data_table_with_signals['10_MA'].values[i+1] < data_table_with_signals['20_MA'].values[i+1])):
            data_table_with_signals['Signal'].iloc[i] = 'Sell'

    # Creating columns for the layout
    col1, col2 = st.columns([0.4, 0.2])

    # Display the full data plot in first column
    with col1:
        st.plotly_chart(fig1)

    # Display the stock data in a table
    news_table = get_news_yahoo(selected_ticker)

    # Apply sentiment scoring to the news data
    parsed_and_scored_news = score_news(news_table)

    final_news = parsed_and_scored_news[['published', 'summary']].copy()
    final_news['published'] = pd.to_datetime(final_news['published'])
    final_news.sort_values(by='published', inplace=True)
    pd.options.display.float_format = '{:%Y-%m-%d}'.format

    from pandas.tseries.offsets import BDay

    def get_trade_open(date):
        curr_date_open = pd.to_datetime(date).floor('d').replace(hour=13, minute=30) - BDay(0)
        curr_date_close = pd.to_datetime(date).floor('d').replace(hour=20, minute=0) - BDay(0)

        prev_date_close = (curr_date_open - BDay()).replace(hour=20, minute=0)
        next_date_open = (curr_date_close + BDay()).replace(hour=13, minute=30)

        if ((pd.to_datetime(date) >= prev_date_close) & (pd.to_datetime(date) < curr_date_open)):
            return curr_date_open
        elif ((pd.to_datetime(date) >= curr_date_close) & (pd.to_datetime(date) < next_date_open)):
            return next_date_open
        else:
            return None

    final_news['Trading_Time'] = final_news['published'].apply(get_trade_open)
    final_news.dropna(inplace=True)
    final_news['Date'] = pd.to_datetime(pd.to_datetime(final_news['Trading_Time']).dt.date)

    vader = SentimentIntensityAnalyzer()
    scores = pd.DataFrame(final_news['summary'].apply(vader.polarity_scores).tolist())
    final_news['compound'] = scores['compound'].values.tolist()
    final_news = final_news[final_news['compound'] != 0].reset_index(drop=True)

    unique_dates = final_news['Date'].unique()
    grouped_dates = final_news.groupby(['Date'])
    keys_dates = list(grouped_dates.groups.keys())

    max_score = []
    min_score = []

    for key in grouped_dates.groups.keys():
        data_group = grouped_dates.get_group(key)
        if data_group["compound"].max() > 0:
            max_score.append(data_group["compound"].max())
        elif data_group["compound"].max() < 0:
            max_score.append(0)

        if data_group["compound"].min() < 0:
            min_score.append(data_group["compound"].min())
        elif data_group["compound"].min() > 0:
            min_score.append(0)

    extreme_score = pd.DataFrame({'Date': keys_dates, 'Min_Score': min_score, 'Max_Score': max_score})
    extreme_score['Final_Score'] = extreme_score[['Min_Score', 'Max_Score']].sum(axis=1)

import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
#from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

def calculate_buy_sell_signals(data, extreme_score):
    Buy_Option = []
    Sell_Option = []

    for i in range(len(extreme_score)):
        if extreme_score['Final_Score'].values[i] > 0.3:  # Optional Threshold
            Buy_Option.append(extreme_score['Date'].iloc[i].date())
        elif extreme_score['Final_Score'].values[i] < -0.3:  # Optional Threshold
            Sell_Option.append(extreme_score['Date'].iloc[i].date())

    return Buy_Option, Sell_Option

def vader_signals(data, Buy_Option, Sell_Option):
    vader_buy = []
    for i in range(len(data)):
        if data.index[i].date() in Buy_Option:
            vader_buy.append(i)

    vader_sell = []
    for i in range(len(data)):
        if data.index[i].date() in Sell_Option:
            vader_sell.append(i)

    return vader_buy, vader_sell

def create_fig2_plot(data, vader_buy, vader_sell, selected_ticker):
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=data.index[-30:], y=data['Adj Close'][-30:], mode='lines', name='Closing Price'))
    fig2.add_trace(go.Scatter(x=data.index[vader_buy][-30:], y=data.loc[data.index[vader_buy][-30:], 'Adj Close'], mode='markers', name='Buy Signal', marker=dict(color='green', size=8)))
    fig2.add_trace(go.Scatter(x=data.index[vader_sell][-30:], y=data.loc[data.index[vader_sell][-30:], 'Adj Close'], mode='markers', name='Sell Signal', marker=dict(color='red', size=8)))
    fig2.update_layout(title=f'Last 30 Days Sentiment Signal for {selected_ticker}', xaxis_title='Date', yaxis_title='Price',
                       legend=dict(orientation="h", y=1.02, x=0.5))  # Move the legend to the bottom
    return fig2


    # Create a new figure
    fig2 = create_fig2_plot(data, vader_buy, vader_sell, selected_ticker)

    # Creating columns for the layout
    col3, col4 = st.columns([0.5, 0.2])

    # Display the full data plot in the first column
    with col3:
         st.plotly_chart(fig2)

    # Display the last 30 days plot in the second column
    # Display the extreme scores table in the fourth column
    with col4:
        st.write("**Extreme Scores Table**")
        # Convert the Date column to string format without the timestamp
        extreme_score['Date'] = extreme_score['Date'].dt.strftime('%Y-%m-%d')
        # Display the extreme scores table with dates only (no timestamp)
        st.write(extreme_score.head())

if __name__ == '__main__':
    analyze_stock()
