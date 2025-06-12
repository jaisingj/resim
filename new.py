import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pytz
import talib
from PIL import Image
from io import BytesIO
import base64

st.set_page_config(page_title="Advanced Stock Dashboard", layout="wide")

# Load API Key
try:
    FMP_API_KEY = st.secrets["fmp"]["api_key"]
except:
    st.error("Please set up your FMP API key in secrets.toml")
    st.stop()

# Sidebar - Tabs and company selection
tabs = st.sidebar.radio("Tabs", ("Recent Data", "Sentiment and Signal", "Financials"))
df_tickers = pd.read_csv('tickers.csv')
company_names = df_tickers['Name'].tolist()
selected_company = st.sidebar.selectbox("Select Company", company_names)
symbol = df_tickers[df_tickers['Name'] == selected_company]['Symbol'].values[0]
selected_name = selected_company
time_period = st.sidebar.radio("Select Time Period", ["1D", "3MO", "1YR", "5YR"], index=0)

# Adjust date if it's a weekend
selected_date = datetime.today()
if selected_date.weekday() >= 5:
    selected_date -= timedelta(days=selected_date.weekday() - 4)

# Helper: Convert image to base64
def image_to_base64(img):
    buffered = BytesIO()
    img.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode()

# Load and inject custom CSS
css_path = "styles.css"
with open(css_path, "r") as file:
    css = f"<style>{file.read()}</style>"
st.markdown(css, unsafe_allow_html=True)

# Header with logo and title
col1, col2, col3 = st.columns([0.4, 0.4, 0.2])
with col1:
    image1 = Image.open('brains.jpeg')
    st.markdown(f"<img src='data:image/jpeg;base64,{image_to_base64(image1)}' style='max-width:30%; align:left; margin-top: -30px;'>", unsafe_allow_html=True)
with col2:
    st.markdown("<h2 style='font-size: 50px; text-align: center; color: navy; margin-top: -20px;'>R.e.s.i.M: 2.0</h2>", unsafe_allow_html=True)
    st.markdown("<h3 style='font-size: 30px; text-align: center; color: green; margin-top: -10px;'>Research & Simulate</h3>", unsafe_allow_html=True)

# Get company metrics
def get_company_metrics(symbol, api_key):
    try:
        quote = f"https://financialmodelingprep.com/api/v3/quote/{symbol}?apikey={api_key}"
        profile = f"https://financialmodelingprep.com/api/v3/company/profile/{symbol}?apikey={api_key}"
        quote_data = requests.get(quote).json()[0]
        profile_data = requests.get(profile).json()
        return {
            'current_price': quote_data.get('price'),
            'change': quote_data.get('change'),
            'changesPercentage': quote_data.get('changesPercentage'),
            'pe_ratio': quote_data.get('pe'),
            'market_cap': quote_data.get('marketCap'),
            '52_week_high': quote_data.get('yearHigh'),
            '52_week_low': quote_data.get('yearLow'),
            'description': profile_data.get('profile', {}).get('description', ''),
            'industry': profile_data.get('profile', {}).get('industry', ''),
            'beta': profile_data.get('profile', {}).get('beta', 'N/A')
        }
    except Exception as e:
        st.error(f"Error fetching company metrics: {e}")
        return {}

# Fetch stock data
def get_historical_data(symbol, time_period, api_key):
    base = "https://financialmodelingprep.com/api/v3"
    if time_period == "1D":
        url = f"{base}/historical-chart/1min/{symbol}?apikey={api_key}"
        data = requests.get(url).json()
        df = pd.DataFrame(data)
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            ny = pytz.timezone('America/New_York')
            df['date'] = df['date'].dt.tz_localize('UTC').dt.tz_convert(ny)
            start = ny.localize(datetime.combine(selected_date, datetime.min.time())).replace(hour=9, minute=30)
            end = ny.localize(datetime.combine(selected_date, datetime.min.time())).replace(hour=16, minute=0)
            df = df[(df['date'] >= start) & (df['date'] <= end)].sort_values('date')
        hist = requests.get(f"{base}/historical-price-full/{symbol}?apikey={api_key}").json()
        hist_df = pd.DataFrame(hist.get('historical', []))
        previous_close = hist_df.iloc[0]['close'] if not hist_df.empty else None
        return df, previous_close
    else:
        days = {"3MO": 90, "1YR": 365, "5YR": 1825}.get(time_period, 365)
        url = f"{base}/historical-price-full/{symbol}?apikey={api_key}"
        data = requests.get(url).json()
        df = pd.DataFrame(data.get('historical', []))
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df = df[df['date'] >= (datetime.now() - timedelta(days=days))].sort_values('date')
            previous_close = df.iloc[0]['close'] if len(df) > 1 else None
        else:
            previous_close = None
        return df, previous_close

# Tooltip helper
def hint(text):
    return f"<span title='{text}'><span style='font-size: 16px; color: red; border-radius: 50%; border: 1px solid grey; padding: 0.5px 8px;'>?</span></span>"

# Render "Recent Data" tab
if tabs == "Recent Data":
    hint_text = hint("Intraday data only available for 1D, daily for 3MO+.")
    st.markdown(f'<div class="title-container" style="margin-top: -4px;"><h3 style="color: navy; font-size: 28px;">Recent Data - {selected_name} {hint_text}</h3></div>', unsafe_allow_html=True)

    # Title styling
    st.markdown("""
        <style>
        .title-container {
            border-top: 1.0px solid #082C9C;  
            border-bottom: 1.0px solid #082C9C; 
            padding: 0.1px;
            background-color: #CEDDF1;
            text-align: center;
            margin-top: 12px; 
            margin-bottom: 3px;
        }
        </style>
    """, unsafe_allow_html=True)




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
    fig.add_trace(go.Scatter(x=df['date'], y=df['macd'], name='MACD', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=df['date'], y=df['macd_signal'], name='Signal', line=dict(color='orange')))
    fig.add_trace(go.Bar(x=df['date'], y=df['macd_hist'], name='Histogram', marker_color=['green' if v >= 0 else 'red' for v in df['macd_hist']]))
    fig.update_layout(title='MACD (12,26,9)', height=300, margin=dict(l=20, r=20, t=40, b=20))
    return fig

def create_rsi_chart(df):
    if df.empty or 'rsi' not in df.columns:
        return None
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['date'], y=df['rsi'], name='RSI', line=dict(color='purple')))
    fig.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought")
    fig.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold")
    fig.update_layout(title='RSI (14)', height=300, yaxis_range=[0, 100], margin=dict(l=20, r=20, t=40, b=20))
    return fig

def plot_main_chart(df, symbol, time_period):
    if df.empty:
        return None

    if time_period == "1D":
        df['time'] = df['date'].dt.strftime('%H:%M')
        fig = px.line(df, x='time', y='close', title=f"{symbol} Intraday Price - {selected_date.strftime('%Y-%m-%d')}")

        # Add Bollinger Bands
        if 'bb_upper' in df.columns and 'bb_lower' in df.columns and 'bb_middle' in df.columns:
            fig.add_scatter(x=df['time'], y=df['bb_upper'], mode='lines', name='Upper Band',
                            line=dict(color='blue', dash='dot'))
            fig.add_scatter(x=df['time'], y=df['bb_middle'], mode='lines', name='Middle Band',
                            line=dict(color='gray', dash='solid'))
            fig.add_scatter(x=df['time'], y=df['bb_lower'], mode='lines', name='Lower Band',
                            line=dict(color='blue', dash='dot'))

        # Optional: Highlight after-hours range (before 9:30 or after 16:00)
        df['hour'] = pd.to_datetime(df['time'], format='%H:%M').dt.hour + pd.to_datetime(df['time'], format='%H:%M').dt.minute / 60
        after_hours = df[(df['hour'] < 9.5) | (df['hour'] > 16)]
        if not after_hours.empty:
            fig.add_scatter(x=after_hours['time'], y=after_hours['close'], mode='lines', name='After-Hours',
                            line=dict(color='orange', dash='dash'))

        hourly_ticks = ["09:30", "10:00", "10:30", "11:00", "11:30", "12:00", "12:30", "13:00",
                        "13:30", "14:00", "14:30", "15:00", "15:30", "16:00"]
        fig.update_layout(
            xaxis_title="Time (Eastern)",
            yaxis_title="Price (USD)",
            height=300,
            margin=dict(l=20, r=20, t=40, b=20),
            xaxis=dict(tickmode='array', tickvals=hourly_ticks, ticktext=hourly_ticks)
        )
    else:
        fig = px.line(df, x='date', y='close', title=f"{symbol} Price Trend - {time_period}")

        # Add Bollinger Bands
        if 'bb_upper' in df.columns and 'bb_lower' in df.columns and 'bb_middle' in df.columns:
            fig.add_scatter(x=df['date'], y=df['bb_upper'], mode='lines', name='Upper Band',
                            line=dict(color='blue', dash='dot'))
            fig.add_scatter(x=df['date'], y=df['bb_middle'], mode='lines', name='Middle Band',
                            line=dict(color='gray', dash='solid'))
            fig.add_scatter(x=df['date'], y=df['bb_lower'], mode='lines', name='Lower Band',
                            line=dict(color='blue', dash='dot'))

        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Price (USD)",
            height=300,
            margin=dict(l=20, r=20, t=40, b=20)
        )

    return fig

def plot_sp500_chart():
    try:
        url = f"https://financialmodelingprep.com/api/v3/historical-price-full/^GSPC?timeseries=100&apikey={FMP_API_KEY}"
        data = requests.get(url).json().get("historical", [])
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        fig = px.line(df.sort_values('date'), x='date', y='close', title="S&P 500 Index Trend")
        fig.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
        return fig
    except:
        return None

def display_metrics(metrics, current_price, previous_close):
    st.markdown("## Key Metrics")
    delta_value = current_price - previous_close if current_price and previous_close else None
    delta_pct = (delta_value / previous_close) * 100 if delta_value else None
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Current Price", f"${current_price:.2f}" if current_price else "N/A", f"{delta_value:.2f} ({delta_pct:.2f}%)" if delta_value else None)
    with col2:
        st.metric("P/E Ratio", f"{metrics.get('pe_ratio', 'N/A')}")
    with col3:
        st.metric("Market Cap", format_market_cap(metrics.get('market_cap')))
    with col4:
        st.metric("52-Week High", f"${metrics.get('52_week_high', 'N/A')}")
    with col5:
        st.metric("52-Week Low", f"${metrics.get('52_week_low', 'N/A')}")

def format_market_cap(market_cap):
    if not market_cap:
        return "N/A"
    if market_cap >= 1e12:
        return f"${market_cap / 1e12:.2f}T"
    elif market_cap >= 1e9:
        return f"${market_cap / 1e9:.2f}B"
    elif market_cap >= 1e6:
        return f"${market_cap / 1e6:.2f}M"
    return f"${market_cap:,.2f}"

def get_company_news(symbol, api_key, limit=5):
    try:
        url = f"https://financialmodelingprep.com/api/v3/stock_news?tickers={symbol}&limit={limit}&apikey={api_key}"
        return requests.get(url).json()
    except Exception as e:
        st.error(f"Error fetching company news: {e}")
        return []

try:
    metrics = get_company_metrics(symbol, FMP_API_KEY)
    df, prev_close = get_historical_data(symbol, time_period, FMP_API_KEY)
    df = calculate_technical_indicators(df)
    display_metrics(metrics, metrics.get('current_price'), prev_close)

    col1, col2 = st.columns([0.3, 0.3])
    with col1:
        chart = plot_main_chart(df, symbol, time_period)
        if chart:
            st.plotly_chart(chart, use_container_width=True)
    with col2:
        macd_chart = create_macd_chart(df)
        if macd_chart:
            st.plotly_chart(macd_chart, use_container_width=True)

    col3, col4 = st.columns([0.3, 0.3])
    with col3:
        rsi_chart = create_rsi_chart(df)
        if rsi_chart:
            st.plotly_chart(rsi_chart, use_container_width=True)
    with col4:
        sp500_fig = plot_sp500_chart()
        if sp500_fig:
            st.plotly_chart(sp500_fig, use_container_width=True)

    col_news, col_desc = st.columns([0.5, 0.5])
    with col_news:
        st.markdown("## Latest News")
        news_items = get_company_news(symbol, FMP_API_KEY)
        if news_items:
            for item in news_items:
                with st.expander(f"{item['title']} - {item['publishedDate'][:10]} ({item['site']})"):
                    st.write(item['text'])
                    st.write(f"[Read more]({item['url']})")
        else:
            st.write("No recent news available")
    with col_desc:
        st.markdown("### Company Description")
        desc = metrics.get('description', 'No description available')
        st.write(desc)

except Exception as e:
    st.error(f"An error occurred: {e}")