import pandas as pd
import plotly.graph_objs as go
import streamlit as st
import yfinance as yf
import datetime as dt
import threading  # Import threading module
import time
import talib
import requests
from io import BytesIO
from bs4 import BeautifulSoup
from datetime import datetime
import base64
import pandas_ta as ta
from plotly.subplots import make_subplots
from pandas.tseries.offsets import BDay
from app import get_news_yahoo, score_news, color_cells
from nltk.sentiment.vader import SentimentIntensityAnalyzer

api_key = st.secrets["fmp"]["api_key"]


def set_sidebar_selectbox_font_size(font_size):
    st.markdown(
        f"""
        <style>
            .sidebar .widget-content .selectbox label span {{
                font-size: {font_size}px !important;
            }}
        </style>
        """,
        unsafe_allow_html=True
    )

# Define a helper function to get the info or display 'N/A' in red
def get_info(info, key):
    return info.get(key, "<span style='color: red;'>N/A</span>")

def display_image(img):
    img_str = image_to_base64(img)
    st.markdown(
        f'<img src="data:image/jpeg;base64,{img_str}" alt="image" style="width: 100%;">', unsafe_allow_html=True)

def display_title(main_title, subtitle):
    st.markdown(
        f"<h1 style='text-align: center;'>{main_title}</h1>", unsafe_allow_html=True)
    st.markdown(
        f"<h2 style='text-align: center;'>{subtitle}</h2>", unsafe_allow_html=True)


def display_selected_dates(start_date, end_date):
    st.markdown(f"<p>Selected Dates: <strong>{start_date}</strong> to <strong>{end_date}</strong></p>",
                unsafe_allow_html=True)


def change_progress_bar_color():
    st.markdown(
        """
        <style>
            .stProgress > div > div > div > div {
                background-color: green;
            }
        </style>
        """,
        unsafe_allow_html=True
    )



def create_download_link(data, filename):
    csv = data.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">Download Data</a>'
    return href

def image_to_base64(img):
    buffered = BytesIO()
    img.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str

def get_color(value):
    return 'green' if value >= 0 else 'red'

def get_info_value(key, info):
    value = info.get(key, 'N/A') if info is not None else 'N/A'
    return f'<span style="color: red;">{value}</span>' if value == 'N/A' else value

def get_float_value(key, info):
    try:
        value = float(info.get(key, 'N/A'))
    except ValueError:  # value was 'N/A' and float('N/A') raises ValueError
        return '<span style="color: red;">N/A</span>'
    return value

def get_stock_industry(symbol):
    try:
        stock = yf.Ticker(symbol)
        stock_info = stock.info
        return stock_info.get('industry', 'N/A')
    except Exception as e:
        print(f"Error fetching industry for {symbol}: {str(e)}")
        return 'N/A'




def hint(text):
    return f"<span title='{text}'><span style='font-size: 16px; color: red; border-radius: 50%; border: 1px solid grey; padding: 0.5px 8px;'>?</span></span>"

def apply_custom_css():
    st.markdown(
        """
<style>
    table {
        width: 100%;
        text-align: center;
    }
    th {
        text-align: center;
    }

</style>
""",
        unsafe_allow_html=True,
    )

def clear_multi():
    st.session_state.symbol_multiselect = []

def color_tiers(val):
    """
    Takes a scalar and returns a string with
    the CSS property `'color: red'` or `'color: green'` depending on the value.
    """
    color = 'red' if '(' in str(val) or str(val) == 'NA' else 'green'
    return 'color: %s' % color

def hint(text):
    return f"<span title='{text}'><span style='font-size: 16px; color: red; border-radius: 50%; border: 1px solid grey; padding: 0.5px 8px;'>?</span></span>"

def apply_custom_css():
    css_path = "styles.css"
    with open(css_path, "r") as file:
        css = f"<style>{file.read()}</style>"
    return css

def get_news_yahoo(ticker):
    try:
        # Get data from Yahoo Finance
        news_data = news.get_yf_rss(ticker)
        # Convert the list of dicts into a DataFrame
        news_table = pd.DataFrame(news_data)
        return news_table
    except Exception as e:
        print(str(e))
        return pd.DataFrame()  # Return an empty DataFrame in case of an error

def color_cells(val):
    if val < 0:
        color = 'red'
    elif val > 0:
        color = 'green'
    else:
        color = 'navy'
    return 'color: %s' % color


# Add this function to your code
def create_download_link(df, filename):
    csv_string = df.to_csv(index=False)
    b64 = base64.b64encode(csv_string.encode()).decode()
    download_link = f'<a href="data:file/csv;base64,{b64}" download="{filename}">Download {filename}</a>'
    return download_link




# ─────────────────────────────
# FMP Fetch
# ─────────────────────────────
def fetch_stock_history_fmp(ticker, start_date, end_date):
    import requests

    try:
        api_key = st.secrets["fmp"]["api_key"]
    except:
        st.error("Please set up your FMP API key in secrets.toml")
        st.stop()

    url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}"
    params = {
        "from": pd.to_datetime(start_date).strftime("%Y-%m-%d"),
        "to": pd.to_datetime(end_date).strftime("%Y-%m-%d"),
        "apikey": api_key
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()
        if "historical" not in data:
            return pd.DataFrame()

        df = pd.DataFrame(data["historical"])
        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)
        df.sort_index(inplace=True)

        df.rename(columns=str.title, inplace=True)  # Capitalize column names
        df['close'] = df['Close']  # Add lowercase alias for indicator calculations

        return df

    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return pd.DataFrame()
def calculate_technical_indicators(df):
    if df.empty:
        return df

    df['close'] = pd.to_numeric(df['close'], errors='coerce')
    df = df.dropna(subset=['close'])

    if len(df) > 26:
        df['macd'], df['macd_signal'], df['macd_hist'] = talib.MACD(df['close'], 12, 26, 9)
    if len(df) > 14:
        df['rsi'] = talib.RSI(df['close'], 14)
    if len(df) > 20:
        bb_upper, bb_middle, bb_lower = talib.BBANDS(df['close'], timeperiod=20)
        df['bb_upper'] = bb_upper
        df['bb_middle'] = bb_middle
        df['bb_lower'] = bb_lower

    return df


def create_macd_chart(df):
    if df.empty or 'macd' not in df.columns:
        return None
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['macd'], name='MACD', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=df.index, y=df['macd_signal'], name='Signal', line=dict(color='orange')))
    fig.add_trace(go.Bar(x=df.index, y=df['macd_hist'], name='Histogram',
                         marker_color=['green' if v >= 0 else 'red' for v in df['macd_hist']]))
    fig.update_layout(title='MACD (12,26,9)', height=300, margin=dict(l=20, r=20, t=40, b=20),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    return fig

def create_rsi_chart(df):
    if df.empty or 'rsi' not in df.columns:
        return None
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['rsi'], name='RSI', line=dict(color='purple')))
    fig.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought")
    fig.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold")
    fig.update_layout(title='RSI (14)', height=300, yaxis_range=[0, 100],
                      margin=dict(l=20, r=20, t=40, b=20))
    return fig
# ─────────────────────────────
# Chart Generator
# ─────────────────────────────
def generate_charts(start_date, end_date, selected_ticker, date_range_option):




    # Cache
    cache_key = f"{selected_ticker}_{start_date}_{end_date}_{date_range_option}"
    if "stock_data_cache" not in st.session_state:
        st.session_state.stock_data_cache = {}

    if cache_key in st.session_state.stock_data_cache:
        df = st.session_state.stock_data_cache[cache_key]
    else:
        df = fetch_stock_history_fmp(selected_ticker, start_date=start_date, end_date=end_date)
        df = calculate_technical_indicators(df)
        st.session_state.stock_data_cache[cache_key] = df

    if df.empty:
        st.warning("No data available for this timeframe.")
        return

    # Plot Price Trend
    fig_price = go.Figure()
    fig_price.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"],
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        name="Price",
        increasing_line_color="green",
        decreasing_line_color="red"
    ))

    if st.sidebar.checkbox("Show 90-day EMA", value=True):
        df["EMA_90"] = df["Close"].ewm(span=90, adjust=False).mean()
        fig_price.add_trace(go.Scatter(
            x=df.index,
            y=df["EMA_90"],
            mode='lines',
            name="90-day EMA",
            line=dict(color='blue', dash='dot', width=1.5)
        ))

    if st.sidebar.checkbox("Show Bollinger Bands", value=True):
        if 'bb_upper' in df.columns and 'bb_lower' in df.columns:
            fig_price.add_trace(go.Scatter(
                x=df.index,
                y=df["bb_upper"],
                mode='lines',
                name="Upper Band",
                line=dict(color='gray', width=1)
            ))
            fig_price.add_trace(go.Scatter(
                x=df.index,
                y=df["bb_lower"],
                mode='lines',
                name="Lower Band",
                line=dict(color='gray', width=1)
            ))

    fig_price.update_layout(
        title=f"{selected_ticker} Price Trend ({date_range_option})",
        xaxis_title="Date",
        yaxis_title="Price",
        xaxis_rangeslider_visible=True,
        legend=dict(orientation="h", x=0.5, y=1.15, xanchor='center'),
        margin=dict(t=40, l=10, r=10, b=10)
    )

    # MACD and RSI charts using updated logic
    macd_chart = create_macd_chart(df)
    rsi_chart = create_rsi_chart(df)

    # S&P 500 placeholder chart (replace with actual S&P 500 data if needed)
    fig_sp500 = go.Figure()
    fig_sp500.add_trace(go.Scatter(x=df.index, y=df["Close"], name="S&P 500"))
    fig_sp500.update_layout(title="S&P 500 Trend", height=300)

    # Layout columns
    col1, col2 = st.columns([0.3, 0.3])

    with col1:
        st.markdown(
            f'<div class="title-container" style="margin-top: -1px;"><h2 style="color: navy; font-size: 20px;">Price Trend</h2></div>',
            unsafe_allow_html=True
        )
        st.plotly_chart(fig_price, use_container_width=True, key="price_trend")

    with col2:
        st.markdown(
             f'<div class="title-container" style="margin-top: -1px;"><h2 style="color: navy; font-size: 20px;">MACD (12,26,9)</h2></div>',
             unsafe_allow_html=True
        )
        if macd_chart:
            st.plotly_chart(macd_chart, use_container_width=True, key="macd_chart")

    col3, col4 = st.columns([0.3, 0.3])

    with col3:
        st.markdown(
            f'<div class="title-container" style="margin-top: -1px;"><h2 style="color: navy; font-size: 20px;">RSI (14)</h2></div>',
            unsafe_allow_html=True
        )
        if rsi_chart:
            st.plotly_chart(rsi_chart, use_container_width=True, key="rsi_chart")

    with col4:
        st.markdown(
            f'<div class="title-container" style="margin-top: -1px;"><h2 style="color: navy; font-size: 20px;">S&P 500 Trend</h2></div>',
            unsafe_allow_html=True
        )
        st.plotly_chart(fig_sp500, use_container_width=True, key="sp500_chart")

def get_stock_info(ticker):
    # Fetching the web page
    url = f"https://finance.yahoo.com/quote/{ticker}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Assuming you have a way to fetch historical_data as a DataFrame
    historical_data = fetch_historical_data(ticker)  # Placeholder for your historical data fetching logic

    # Parsing the data from the web page
    tables = soup.find_all('table')
    data = {}
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            columns = row.find_all('td')
            if len(columns) >= 2:
                name = columns[0].text.strip()
                value = columns[1].text.strip()
                data[name] = value

    # Extracting specific information
    fifty_two_week_range = data.get('52 Week Range')
    fifty_two_week_low = fifty_two_week_range.split(' - ')[0] if fifty_two_week_range else None
    fifty_two_week_high = fifty_two_week_range.split(' - ')[1] if fifty_two_week_range else None
    current_price = "{:.2f}".format(get_last_price(ticker))  # Make sure get_last_price function is defined
    previous_close = historical_data['Close'].iloc[-2] if len(historical_data) > 1 else None


    return {
        "Beta": data.get('Beta (5Y Monthly)'),
        "Market Cap": data.get('Market Cap'),
        "P/E Ratio": data.get('PE Ratio (TTM)'),
        "Dividend Yield": data.get('Forward Dividend & Yield 4'),
        "52-Week High": fifty_two_week_high,
        "52-Week Low": fifty_two_week_low,
        "Current Price": current_price,
        "Previous Day Close": previous_close,
        "Company Description": display_company_description(ticker)  # Assuming you have this function defined elsewhere
    }




def calculate_stock_sentiment(symbol, api_key, news_limit=10):
    """
    Fetches recent news for the stock and calculates average sentiment.

    Parameters:
        symbol (str): Stock symbol (e.g., "AAPL")
        api_key (str): FMP API Key
        news_limit (int): Number of news articles to analyze

    Returns:
        dict: {'average_sentiment': float, 'article_scores': List[dict]}
    """
    url = f"https://financialmodelingprep.com/api/v3/stock_news?tickers={symbol}&limit={news_limit}&apikey={api_key}"
    try:
        response = requests.get(url)
        news_data = response.json()

        analyzer = SentimentIntensityAnalyzer()
        article_scores = []

        for item in news_data:
            text = f"{item['title']} {item['text']}"
            score = analyzer.polarity_scores(text)['compound']
            article_scores.append({
                'date': item['publishedDate'],
                'title': item['title'],
                'score': score
            })

        avg_sentiment = sum(a['score'] for a in article_scores) / len(article_scores) if article_scores else 0.0
        return {'average_sentiment': avg_sentiment, 'article_scores': article_scores}

    except Exception as e:
        return {'error': str(e)}

def display_stock_data(get_stock_info):
    col1, col2, col3, col4, col5 = st.columns(5)

    # Current Price with Arrow
    with col1:
        current_price = stock_info["Current Price"]      
        #price_diff = float(current_price) - float(previous_close)
        #color = "green" if price_diff > 0 else "red"
        #arrow = "&#9650;" if price_diff >= 0 else "&#9660;"
        
        st.markdown(
            f"**Current price**<br>"
            #f"{current_price} &nbsp; <span style='color:{color};'>{arrow} {'%.2f' % price_diff}</span>",
            #unsafe_allow_html=True
        )

    # Market Cap
    with col2:
        market_cap = stock_info["Market Cap"]
        st.write("Market Cap")
        st.write(market_cap)

    # PE Ratio
    with col3:
        pe_ratio = stock_info["P/E Ratio"]
        st.write("PE Ratio")
        st.write(pe_ratio)

    # 52 Week High
    with col4:
        fifty_two_week_high = stock_info["52-Week High"]
        st.write("52 Week High")
        st.write(fifty_two_week_high)

    # 52 Week Low
    with col5:
        fifty_two_week_low = stock_info["52-Week Low"]
        st.write("52 Week Low")
        st.write(fifty_two_week_low)





def display_stock_info(get_stock_info, get_float_value):
    # Splitting the container into six columns
    col1, col2, col3, col4, col5, col6 = st.columns(
        [0.4, 0.4, 0.4, 0.4, 0.4, 0.4])

    with col1:
        current_price = get_stock_info("current_Price")
        previous_close = get_info_value("previousClose", info)
        display_current_price(current_price, previous_close)

    with col2:
        market_cap = get_info_value("marketCap", info)
        display_market_cap(market_cap)

    with col3:
        pe_ratio = get_float_value("trailingPE", info)
        display_pe_ratio(pe_ratio)

    with col4:
        revenue_growth = get_info_value("revenueGrowth", info)
        display_revenue_growth(revenue_growth)

    with col5:
        fifty_two_week_high = get_info_value("fiftyTwoWeekHigh", info)
        st.markdown(f"<p class='big-label'>52 Week High</p>",
                    unsafe_allow_html=True)
        st.markdown(
            f"<p class='small-value'>{fifty_two_week_high}</p>", unsafe_allow_html=True)

    with col6:
        fifty_two_week_low = get_info_value("fiftyTwoWeekLow", info)
        st.markdown(f"<p class='big-label'>52 Week Low</p>",
                    unsafe_allow_html=True)
        st.markdown(
            f"<p class='small-value'>{fifty_two_week_low}</p>", unsafe_allow_html=True)




def display_market_cap(market_cap):
    if market_cap != '<span style="color: red;">N/A</span>':
        if isinstance(market_cap, (int, float)) and market_cap > 0:
            market_cap = float(market_cap) / 1e9  # Convert to billions
            # Format as "X.XX BN"
            market_cap = f"${'{:,.2f}'.format(market_cap)}BN"
        else:
            market_cap = 'N/A'
    st.markdown(f"<p class='big-label';background-color: #CEDDF1; color: navy>Market Cap</p>",
                unsafe_allow_html=True)
    st.markdown(
        f"<p class='small-value'>{market_cap}</p>", unsafe_allow_html=True)


def display_pe_ratio(pe_ratio):
    if pe_ratio != '<span style="color: red;">N/A</span>':
        st.markdown(f"<p class='big-label'>PE Ratio</p>",
                    unsafe_allow_html=True)
        st.markdown(
            f"<p class='small-value'>{pe_ratio:.2f}</p>", unsafe_allow_html=True)
    else:
        st.markdown(f"<p class='big-label'>PE Ratio</p>",
                    unsafe_allow_html=True)
        st.markdown(
            f"<p class='small-value'>{pe_ratio}</p>", unsafe_allow_html=True)


def display_revenue_growth(revenue_growth):
    if revenue_growth != '<span style="color: red;">N/A</span>':
        revenue_growth = f"{revenue_growth * 100:.2f}%"  # Convert to percentage
        st.markdown(f"<p class='big-label'; color: #CEDDF1; background-color: navy>Revenue Growth</p>",
                    unsafe_allow_html=True)
        st.markdown(
            f"<p class='small-value'>{revenue_growth}</p>", unsafe_allow_html=True)
    else:
        st.markdown(f"<p class='big-label'; color: #CEDDF1; background-color: navy>Revenue Growth</p>",
                    unsafe_allow_html=True)
        st.markdown(
            f"<p class='small-value'>{revenue_growth}</p>", unsafe_allow_html=True)



def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Sheet1', index=False)
    writer.close()  # This is the correct method to finalize the Excel file
    processed_data = output.getvalue()
    return processed_data

def get_table_download_link(df, text, filename):
    """Generates a link allowing the data in a given pandas dataframe to be downloaded
    in:  dataframe
    out: download link
    """
    val = to_excel(df)
    b64 = base64.b64encode(val)  # val looks like b'...'
    return f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64.decode()}" download="{filename}.xlsx">{text}</a>'


def plot_last_30_days_sentiment(selected_ticker, start_date):
    # Automatically set start date to 30 days ago from today
    end_date = dt.datetime.now()
    start_date = end_date - dt.timedelta(days=30)

    #data = yf.download(selected_ticker, start=start)
    
    # Retrieve and score news data
    news_table = get_news_yahoo(st.session_state.selected_ticker)
    parsed_and_scored_news = score_news(news_table)
    final_news = parsed_and_scored_news[['published', 'summary']].copy()
    final_news['published'] = pd.to_datetime(final_news['published'])
    final_news.sort_values(by='published', inplace=True)
    final_news['Trading_Time'] = final_news['published'].apply(get_trade_open)
    final_news.dropna(inplace=True)
    final_news['Date'] = pd.to_datetime(pd.to_datetime(final_news['Trading_Time']).dt.date)
    
    # Perform sentiment analysis
    vader = SentimentIntensityAnalyzer()
    scores = pd.DataFrame(final_news['summary'].apply(vader.polarity_scores).tolist())
    final_news['compound'] = scores['compound'].values.tolist()
    final_news = final_news[final_news['compound'] != 0].reset_index(drop=True)
    
    unique_dates = final_news['Date'].unique()
    grouped_dates = final_news.groupby(['Date'])
    
    max_score = []
    min_score = []
    
    for key in grouped_dates.groups.keys():
        data_group = grouped_dates.get_group(key)
        max_score.append(data_group["compound"].max())
        min_score.append(data_group["compound"].min())
        
    extreme_score = pd.DataFrame({'Date': unique_dates, 'Min_Score': min_score, 'Max_Score': max_score})
    extreme_score['Final_Score'] = extreme_score[['Min_Score','Max_Score']].sum(axis=1)
    
    Buy_Option = [d.date() for i, d in extreme_score.iterrows() if d['Final_Score'] > 0.3]
    Sell_Option = [d.date() for i, d in extreme_score.iterrows() if d['Final_Score'] < 0.3]
    
    vader_buy = [i for i in range(len(data)) if data.index[i].date() in Buy_Option]
    vader_sell = [i for i in range(len(data)) if data.index[i].date() in Sell_Option]
    
    # Create the plot for the last 30 days
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=data.index[-30:], y=data['Adj Close'][-30:], mode='lines', name='Closing Price'))
    fig2.add_trace(go.Scatter(x=data.index[vader_buy][-30:], y=data.loc[data.index[vader_buy][-30:], 'Adj Close'], mode='markers', name='Buy Signal', marker=dict(color='green', size=8)))
    fig2.add_trace(go.Scatter(x=data.index[vader_sell][-30:], y=data.loc[data.index[vader_sell][-30:], 'Adj Close'], mode='markers', name='Sell Signal', marker=dict(color='red', size=8)))
    fig2.update_layout(title='Last 30 Days Sentiment Signal', xaxis_title='Date', yaxis_title='Price',
                       legend=dict(orientation="h", y=1.02, x=0.5))
    
    st.plotly_chart(fig2)
    
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

def get_stock_industry(symbol):
    try:
        stock = yf.Ticker(symbol)
        stock_info = stock.info
        historical_data = stock.history(period='2d')
        return stock_info.get('industry', 'N/A')
    except Exception as e:
        print(f"Error fetching industry for {symbol}: {str(e)}")
        return 'N/A'


# Function to generate a download link for a DataFrame as a CSV file
def get_table_download_link(df, text, filename):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # Convert to base64 string
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}.csv" style="background-color: navy; color: white; padding: 8px 16px; border-radius: 4px; text-decoration: none;">{text}</a>'
    return href


def simulate_future_value(symbol, target_percentage, target_dollar_amount, custom_investment=0):
    today = datetime.date.today()

    ticker_df = pd.read_csv('tickers.csv')
    names = ticker_df['Name'].tolist()

    symbol_index = names.index(symbol)
    if symbol_index >= 0:
        symbol = ticker_df['Symbol'][symbol_index]
    else:
        print(f"No symbol found for {symbol}. Skipping...")
        return None

    ticker = yf.Ticker(symbol)
    stock_info = ticker.history(period='1d', interval='1m')
    stock_info_p = ticker.history(period="2d")


    if not stock_info.empty:
        current_price = stock_info['Close'][0]
        target_price = current_price + (current_price * (target_percentage / 100))  # Calculate the target share price
        shares_bought = target_dollar_amount / current_price
        target_dollar_amount_after_growth = target_price * shares_bought
        gains = target_dollar_amount_after_growth - custom_investment

        gains_formatted = f'<span style="color: {"red" if gains < 0 else "green"};">({abs(gains):.2f})</span>' if gains != 0 else "0.00"


        return {
            'Company': symbol,
            'Industry': get_stock_industry(symbol),
            'Current Price': current_price,
            'Target Share Price': target_price,  # Add target share price to the result
            'Target Percentage': target_percentage,
            'Custom Investment': custom_investment,  # Include the custom investment amount
            'Target Dollar Amount': target_dollar_amount,
            'Shares': shares_bought,
            'Target Dollar Amount After Growth': target_dollar_amount_after_growth,
            'Gains': gains_formatted,  # Use the formatted gains value here
        }
    else:
        print(f"No data found for {symbol}. Skipping...")
        return None


def get_last_price(ticker):
    stock = yf.Ticker(ticker)
    todays_data = stock.history(period='1d')
    historical_data = stock.history(period='2d')
    return todays_data['Close'][0]

def get_stock_info(ticker):
    url = f"https://finance.yahoo.com/quote/{ticker}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    tables = soup.find_all('table')
    
    data = {}
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            columns = row.find_all('td')
            if len(columns) >= 2:
                name = columns[0].text.strip()
                value = columns[1].text.strip()
                data[name] = value

    fifty_two_week_range = data.get('52 Week Range')
    fifty_two_week_low = fifty_two_week_range.split(' - ')[0] if fifty_two_week_range else None
    fifty_two_week_high = fifty_two_week_range.split(' - ')[1] if fifty_two_week_range else None
    current_price = "{:.2f}".format(get_last_price(ticker))

    return {
        "Beta": data.get('Beta (5Y Monthly)'),
        "Market Cap": data.get('Market Cap'),
        "P/E Ratio": data.get('PE Ratio (TTM)'),
        "Dividend Yield": data.get('Forward Dividend & Yield 4'),
        "52-Week High": fifty_two_week_high,
        "52-Week Low": fifty_two_week_low,
        "Current Price": current_price,
        "Company Description": get_company_description_from_iex(ticker)
    }


def display_current_price(col, current_price, previous_close):
    try:
        current_price_float = float(current_price)
        previous_close_float = float(previous_close)
    except (TypeError, ValueError):
        col.markdown(
            f"<p style='color: navy;'>Current Price</p>"
            f"<p style='color:black;'>{current_price}</p>",
            unsafe_allow_html=True
        )
        col.markdown(
            f"<p style='color:red; font-size:22px; margin-top: -2px;' class='price-difference'>{previous_close}</p>",
            unsafe_allow_html=True
        )
        return

    


def get_stock_industry(symbol):
    try:
        stock = yf.Ticker(symbol)
        stock_info = stock.info
        return stock_info.get('industry', 'N/A')
    except Exception as e:
        print(f"Error fetching industry for {symbol}: {str(e)}")
        return 'N/A'

def get_table_download_link(df, text, filename):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # Convert to base64 string
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}.csv" style="background-color: navy; color: white; padding: 8px 16px; border-radius: 4px; text-decoration: none;">{text}</a>'
    return href

def simulate_future_value(symbol, target_percentage, Investment, custom_investment=0):
    today = dt.date.today()

    ticker_df = pd.read_csv('tickers.csv')
    names = ticker_df['Name'].tolist()
    sec = ticker_df['Sector'].tolist()  # Use ticker_df here
    ind = ticker_df['Industry'].tolist()

    company_name = names[names.index(symbol)]
    company_sec = sec[names.index(symbol)]  # Use names.index to find the sector
    company_ind = ind[names.index(symbol)]  # Use names.index to find the industry

    symbol_index = names.index(symbol)
    if symbol_index >= 0:
        symbol = ticker_df['Symbol'][symbol_index]
    else:
        print(f"No symbol found for {symbol}. Skipping...")
        return None

    ticker = yf.Ticker(symbol)
    stock_info = ticker.history(period="1d")

    if not stock_info.empty:
        current_price = stock_info['Close'][0]
        # Convert the target_percentage to a float
        target_percentage = float(target_percentage)
        target_price = current_price * (1 + (target_percentage/100))  # Calculate the target share price
        shares_bought = Investment / current_price
        Value_after_growth = target_price * shares_bought
        gains =  Value_after_growth - Investment

        return {
            'Company': company_name,
            'Industry': company_ind,
	    'Sector':company_sec,
            'Investment': Investment,
            'Current Price': current_price,
            'Shares': shares_bought,
            'Target Percentage': target_percentage,
            'Target Share Price': target_price,  # Add target share price to the result
            'Custom Investment': custom_investment,  # Include the custom investment amount                
            'Potential Gain/Loss':  Value_after_growth,
            'Gains': gains,
        }
    else:
        print(f"No data found for {symbol}. Skipping...")
        return None


def simulate_portfolio():
    # Load the tickers.csv file
    tickers_df = pd.read_csv('tickers.csv')

    col1, col2, col3, col4 = st.columns([0.4, 0.4, 0.4, 0.4])

    with col2:
        # Create a multiselect dropdown for selecting companies
        selected_companies = st.multiselect("Select one or more Company:", tickers_df['Name'])

    # Create a dictionary to store Purchase prices and initialize with default value
    Purchase_prices = {company: 0.01 for company in selected_companies}

    # Create a dictionary to store sell prices and initialize with 0
    sell_prices = {company: 0.01 for company in selected_companies}

    # Create a dictionary to store last close prices and dates
    last_close_prices = {company: {'price': 0.01, 'date': None} for company in selected_companies}

    with col2:
        # Create a checkbox to automatically populate Buy Price with Last Close Price
        auto_populate_buy_price = st.checkbox("Use Last Close Price as Buy Price")

        # Create a checkbox to automatically populate Sell Price with Last Close Price
        auto_populate_sell_price = st.checkbox("Use Last Close Price as Sell Price")

    # Create columns layout to put Buy and Sell input boxes side by side
    col1, col2, col3, col4 = st.columns([0.2, 0.2, 0.2, 0.3])

    # Create input boxes for Buy and Sell prices based on user selection
    for company in selected_companies:
        with col2:
            if auto_populate_buy_price:
                # Automatically fetch the last close price and date from Yahoo Finance for Buy Price
                selected_symbol = tickers_df[tickers_df['Name'] == company]['Symbol'].values[0]
                stock_data = yf.download(selected_symbol, period="1d")
                if not stock_data.empty:
                    last_close_prices[company]['price'] = stock_data['Close'].iloc[0]
                    last_close_prices[company]['date'] = stock_data.index[0].strftime('%b %d, %y')
                    Purchase_prices[company] = last_close_prices[company]['price']
            else:
                # Allow user input for Buy price
                Purchase_prices[company] = st.number_input(f"Enter Buy Price for {company}", min_value=0.01, step=0.01, value=Purchase_prices[company])

        with col3:
            if auto_populate_sell_price:
                # Automatically fetch the last close price and date from Yahoo Finance for Sell Price
                selected_symbol = tickers_df[tickers_df['Name'] == company]['Symbol'].values[0]
                stock_data = yf.download(selected_symbol, period="1d")
                if not stock_data.empty:
                    last_close_prices[company]['price'] = stock_data['Close'].iloc[0]
                    last_close_prices[company]['date'] = stock_data.index[0].strftime('%b %d, %y')
                    sell_prices[company] = last_close_prices[company]['price']
            else:
                # Allow user input for Sell price
                sell_prices[company] = st.number_input(f"Enter Sell Price for {company}", min_value=0.01, step=0.01, value=sell_prices[company])

    col1, col2, col3, col4 = st.columns([0.2, 0.9, 0.5, 0.2])
    # Create input box for the Simulate button
    with col3:
        simulate_button = st.button("Simulate")

    # Define an empty DataFrame for results
    results_df = None

    # Check if the Simulate button is clicked
    if simulate_button:
        results = []

        for selected_company in selected_companies:
            Purchase_price = Purchase_prices[selected_company]
            sell_price = sell_prices[selected_company]
            last_close_price = last_close_prices[selected_company]['price']
            last_close_date = last_close_prices[selected_company]['date']

            formatted_results = {
                "Company Name": selected_company,
                "Industry": tickers_df[tickers_df['Name'] == selected_company]['Industry'].values[0],
                "Purchase Price($)": "{:.2f}".format(Purchase_price),
                "Sell Price($)": "{:.2f}".format(sell_price),
                "Gain/Loss($)": "{:.2f}".format(sell_price - Purchase_price),
                "Gain/Loss(%)": "{:.2f}".format(((sell_price - Purchase_price) / Purchase_price) * 100, 2)
            }

            # Include "Last Close Price" and "Last Close Date" only if auto_populate_sell_price is active
            if auto_populate_sell_price:
                formatted_results["Last Close Price"] = "{:.2f}".format(last_close_price) if last_close_price is not None else None
                formatted_results["Last Close Date"] = last_close_date if last_close_date is not None else None

            results.append(formatted_results)

        # Update the results DataFrame
        results_df = pd.DataFrame(results)

    # Determine if the simulation results in profit or loss
    if results_df is not None:
        total_buy = sum(Purchase_prices.values())
        total_gain_loss = sum(sell_prices.values()) - total_buy
        total_gain_loss_percentage = (total_gain_loss / total_buy) * 100 if total_buy > 0 else 0
        result_color = "green" if total_gain_loss >= 0 else "red"
        result_text = "Gain" if total_gain_loss >= 0 else "Loss"

    # Display the result statement and format the numbers with HTML color tags
    if results_df is not None:
        with col2:
            st.markdown(f"### Simulation Results\n\nThe current portfolio mix and projected stock prices will result in a "
                        f"<font color='{result_color}'>{result_text} of</font>  "
                        f"<font color='{result_color}'>{total_gain_loss:.2f} ({total_gain_loss_percentage:.2f}%)</font>.",
                        unsafe_allow_html=True)

    # Display the total values only if results_df is defined
    if results_df is not None:
        with col2:
            st.table(results_df)

    # Change the column title color to navy
    st.markdown(
        """
        <style>
        table th {
            color: navy !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


# Define custom CSS for the HTML table outside the function
custom_css = """
<style>
    table {width: 60%;}
    th, td {text-align: center; font-size: 14pt; min-width: 100px;}
    th {background-color: #CEDDF1;}
</style>
"""

# Call the function to simulate the portfolio
#simulate_portfolio()

