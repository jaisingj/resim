import streamlit as st
#st.set_page_config(layout="wide")  # Enable wide mode

import pandas as pd
import numpy as np
import plotly.express as px
import datetime as dt
from pandas.tseries.offsets import BDay
from yahoo_fin import news
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk
from dateutil.parser import parse
import yfinance as yf

# Download required NLTK data
nltk.download('vader_lexicon')

# Load tickers from Tickers.csv
# Load tickers from Tickers.csv (must have columns "Name" and "Symbol")
df_tickers = pd.read_csv("Tickers.csv")

# Sidebar: Select a company by its Name using a unique key.
selected_name = st.sidebar.selectbox("Select a company", df_tickers["Name"], key="company_name_select")

# Look up the corresponding ticker symbol and store it in session_state.
selected_ticker = df_tickers.loc[df_tickers["Name"] == selected_name, "Symbol"].iloc[0]
st.session_state["selected_ticker"] = selected_ticker

# Optionally, if you want to store the selected company name as well, use a different key:
st.session_state["company_name"] = selected_name


# Custom CSS
st.markdown("""
<style>
.data-table td, .data-table th {
    border: 1px solid #ddd;
    padding: 8px;
}
.data-table th {
    background-color: #4CAF50;
    color: white;
    text-align: left;
}
.data-table td:first-child {
    white-space: nowrap;
    width: 120px;
}
.data-table td:last-child {
    width: 300px;
}
.chart-title {
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Utility Functions
# ---------------------------
def color_cells(val):
    if val < 0:
        return 'color: red'
    elif val > 0:
        return 'color: green'
    else:
        return 'color: navy'

def get_news_yahoo(ticker):
    try:
        news_data = news.get_yf_rss(ticker)
        news_table = pd.DataFrame(news_data)
        news_table.dropna(subset=['title', 'published', 'summary', 'link'], inplace=True)
        news_table = news_table[(news_table['title'] != '') &
                                (news_table['published'] != '') &
                                (news_table['summary'] != '') &
                                (news_table['link'] != '')]
        news_table['article_link'] = news_table['link']
        return news_table
    except Exception as e:
        st.write("Error fetching news:", e)
        return pd.DataFrame()

def score_news(parsed_news_df):
    vader = SentimentIntensityAnalyzer()
    scores = parsed_news_df['title'].apply(vader.polarity_scores).tolist()
    scores_df = pd.DataFrame(scores)
    parsed_and_scored_news = parsed_news_df.join(scores_df, rsuffix='_right')
    parsed_and_scored_news = parsed_and_scored_news.rename(columns={"compound": "sentiment_score"})
    return parsed_and_scored_news

# ---------------------------
# Hint and Title Markdown
# ---------------------------
def hint(text):
    return f"<span title='{text}'><span style='font-size: 18px; top: -15px; bottom: -25px; color: red; border-radius: 50%; border: 2px solid grey; padding: 0.5px 8px;'>?</span></span>"

st.markdown("""
    <style>
    .title-container {
        border-top: 1.0px solid #082C9C;  
        border-bottom: 1.0px solid #082C9C; 
        padding: 0.1px;
        background-color: #CEDDF1;
        text-align: center;
        margin-top: 12px; 
        margin-bottom: 4px;
    }
    /* Hide the form border */
    .stForm > div > div:first-child {
         border: none;
    }
    </style>
""", unsafe_allow_html=True)

hint_text = hint("This section allows you to view the performance of a mix of different stocks based on the industry and sector. These are based on research that looks at some of the best performing mutual funds which use similar holdings in their portfolio. Return is a theme’s performance expressed as a percentage change in its price for the past 365 days and the cumulative return is based on the weights assigned.")
st.markdown(f'<div class="title-container" style="margin-top: -40px;"><h3 style="color: navy; font-size: 30px; margin-top: 4px;">Sector Analysis {hint_text}</h3></div>', unsafe_allow_html=True)

# ---------------------------
# Sentiment Chart Function
# ---------------------------
def display_sentiment_chart(ticker):
    try:
        parsed_news_df = get_news_yahoo(ticker)
        parsed_and_scored_news = score_news(parsed_news_df)
        if parsed_and_scored_news.empty:
            st.write("No news data available for sentiment analysis.")
            return
        # Prepare chart data
        chart_data = parsed_and_scored_news[['published', 'neg', 'neu', 'pos', 'sentiment_score']].rename(
            columns={
                "published": "PubDate",
                "neg": "Negative",
                "neu": "Neutral",
                "pos": "Positive",
                "sentiment_score": "Score"
            }
        )
        chart_data['PubDate'] = chart_data['PubDate'].apply(lambda x: parse(x))
        daily_scores = chart_data.set_index('PubDate').resample('D').mean()
        fig = px.bar(
            daily_scores,
            x=daily_scores.index,
            y='Score',
            color='Score',
            color_continuous_scale=['red', 'green'],
            range_color=[-1, 1]
        )
        fig.update_layout(
            showlegend=False,
            title_text='Daily Average Sentiment Score',
            title_x=0.5,
            title_font=dict(size=20, color='navy')
        )
        fig.update_xaxes(tickformat="%b %d")
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.write("Error displaying sentiment chart:", e)

# ---------------------------
# Sentiment Data Table Function
# ---------------------------
def display_sentiment_data_table(ticker):
    try:
        parsed_news_df = get_news_yahoo(ticker)
        parsed_and_scored_news = score_news(parsed_news_df)
        if parsed_and_scored_news.empty:
            st.write("No news data available for sentiment analysis.")
            return
        table_data = parsed_and_scored_news[['published', 'sentiment_score', 'summary']].rename(
            columns={
                "published": "PubDate",
                "sentiment_score": "Score",
                "summary": "Summary"
            }
        )
        table_data['PubDate'] = table_data['PubDate'].apply(lambda x: parse(x)).dt.strftime('%b %d')
        table_data['Summary'] = table_data['Summary'].str.slice(0, 150) + '...'
        table_data = table_data.head(10)
        styled_table = table_data.style \
            .format({"Score": "{:.2f}"}) \
            .applymap(color_cells, subset=['Score']) \
            .set_table_attributes("class='data-table'") \
            .set_table_styles([
                {'selector': 'th', 'props': [('background-color', '#CEDDF1'), ('color', 'black'), ('font-size', '18px')]},
                {'selector': 'td', 'props': [('font-size', '16px')]}
            ])
        st.table(styled_table)
    except Exception as e:
        st.write("Error displaying sentiment data table:", e)

# ---------------------------
# Final Signal Function (display_fig2)
# ---------------------------
def display_fig2(selected_ticker):
    # Download the last 180 days of trading data
    end_date = dt.datetime.now()
    start_date = end_date - dt.timedelta(days=180)
    data = yf.download(selected_ticker, start=start_date, end=end_date)

    # Calculate moving averages (retained but not used for charting)
    data['10_MA'] = data['Close'].rolling(window=10).mean()
    data['20_MA'] = data['Close'].rolling(window=20).mean()

    # Prepare the data table (dropping 'Volume') and normalize the index
    data_table = data.drop('Volume', axis=1)
    data_table.index = data_table.index.normalize()

    # Process news for sentiment-based signals if available
    news_table = get_news_yahoo(selected_ticker)
    if not news_table.empty:
        parsed_and_scored_news = score_news(news_table)
        final_news = parsed_and_scored_news[['published', 'summary']].copy()
        final_news['published'] = pd.to_datetime(final_news['published'])
        final_news.sort_values(by='published', inplace=True)
        pd.options.display.float_format = '{:%Y-%m-%d}'.format

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
        final_news['Date'] = pd.to_datetime(final_news['Trading_Time']).dt.date

        vader = SentimentIntensityAnalyzer()
        scores = pd.DataFrame(final_news['summary'].apply(vader.polarity_scores).tolist())
        final_news['compound'] = scores['compound'].values.tolist()
        final_news = final_news[final_news['compound'] != 0].reset_index(drop=True)

        grouped_dates = final_news.groupby(['Date'])
        keys_dates = list(grouped_dates.groups.keys())

        max_score = []
        min_score = []
        for key in grouped_dates.groups.keys():
            data_group = grouped_dates.get_group(key)
            max_val = data_group["compound"].max()
            min_val = data_group["compound"].min()
            max_score.append(max_val if max_val > 0 else 0)
            min_score.append(min_val if min_val < 0 else 0)
        extreme_score = pd.DataFrame({'Date': keys_dates, 'Min_Score': min_score, 'Max_Score': max_score})
        extreme_score['Final_Score'] = extreme_score[['Min_Score', 'Max_Score']].sum(axis=1)

        # Display only the final signal table (no chart)
        st.markdown("<h5 style='color: navy; text-align: center;'>Final Signal Score (Buy: >0.3 | Sell: <0.3)</h5>", unsafe_allow_html=True)
    
        for col in ['Min_Score', 'Max_Score', 'Final_Score']:
            extreme_score[col] = pd.to_numeric(extreme_score[col], errors='coerce')
        extreme_score['Date'] = pd.to_datetime(extreme_score['Date']).dt.strftime('%b %d')
        extreme_score[['Min_Score', 'Max_Score', 'Final_Score']] = extreme_score[['Min_Score', 'Max_Score', 'Final_Score']].applymap("{:.2f}".format)
        table = extreme_score.head()
        table = table.style.set_table_styles([
            {'selector': 'th', 'props': [('background-color', '#CEDDF1'), ('color', 'black'), ('font-size', '20px')]},
            {'selector': 'td', 'props': [('font-size', '20px')]}
        ])
        table = table.applymap(lambda x: f"color: {'green' if float(x) > 0 else 'red'}", subset=['Final_Score'])
        st.table(table)
    else:
        st.write("No news data available for sentiment-based trading signals.")

# ---------------------------
# Global Function: analyze_sentiment
# ---------------------------
def analyze_sentiment(ticker=None):
    """
    Global function to analyze sentiment.
    Uses the ticker from the argument if provided; otherwise, uses st.session_state['selected_ticker'].
    Displays the final signal table and sentiment data table full width,
    with the sentiment score chart in the third column.
    """
    if ticker is None:
        ticker = st.session_state.get('selected_ticker', '')
    if not ticker:
        st.write("No ticker selected.")
        return

    # Display the final signal table (full width)
    st.markdown("<h4 style='color: navy; text-align: center;'>Final Signal Score</h4>", unsafe_allow_html=True)
    display_fig2(ticker)

    # Create three columns and only use the third column for the sentiment score chart
    col1, _, col3 = st.columns([1, 0.01,0.1])
    with col1:
        st.markdown("<h4 style='color: navy; text-align: center;'>Sentiment Score Chart</h4>", unsafe_allow_html=True)
        display_sentiment_chart(ticker)

    # Display the sentiment data table below the columns (full width)
    st.markdown("<h4 style='color: navy; text-align: center;'>Sentiment Data</h4>", unsafe_allow_html=True)
    display_sentiment_data_table(ticker)

    st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)