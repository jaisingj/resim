import streamlit as st
st.set_page_config(layout="wide")
from imports import *
import pandas as pd
import stock_utils
import numpy as np
# import yahoo_fin as yf
import datetime as dt
import requests
import pytz
from PIL import Image
from io import BytesIO
import base64
import os
import plotly.graph_objects as go
from simulator import stock_simulation
# from analyze_trend import calculate_buy_sell_signals, create_fig2_plot
from app import analyze_sentiment
from llama import run_llama_chat
from listing import analyze_stock_data
from finfo import financial_dashboard_function
from functions import generate_charts
from theme import run_sector_returns
from yahoo_fin import news
from fmp_helper import fetch_stock_history_fmp

api_key = st.secrets["fmp"]["api_key"]

if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = None

hint_text = ""

page = st.sidebar.radio("Choose one", ['Analysis', 'ChatBot', 'Custom Listings', 'Sectors', 'FAQ'])

def get_jsonparsed_data(url):
    response = requests.get(url)
    if response.status_code == 200:
        response_data = response.json()[:5]
        results = []
        for data in response_data:
            result = {
                "Year": int(data.get('date', 'N/A')[:4]),
                "Revenue": float(data.get('revenue', 0) / 10 ** 9),
                "Net Income": float(data.get('netIncome', 0) / 10 ** 9),
                "OpExp": float(data.get('operatingExpenses', 0) / 10 ** 9),
                "EBITDA": float(data.get('ebitda', 0) / 10 ** 9),
                "EPS": data.get('eps', 'N/A'),
            }
            results.append(result)
        return results
    else:
        return None

def hint(text):
    return f"<span title='{text}'><span style='font-size: 16px; color: red; border-radius: 50%; border: 1px solid grey; padding: 0.5px 8px;'>?</span></span>"

upload_option_radio = ""

if page == 'Analysis':
    css_path = "styles.css"
    with open(css_path, "r") as file:
        css = f"<style>{file.read()}</style>"
    st.markdown(css, unsafe_allow_html=True)

    def image_to_base64(img):
        buffered = BytesIO()
        img.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return img_str

    df_tickers = pd.read_csv('tickers.csv')
    options = df_tickers['Symbol'].tolist()
    col1, col2, col3, col4 = st.columns([0.5, 0.6, 0.3, 0.3])

    with col1:
        image1 = Image.open('brains.jpeg')
        st.markdown(f"<img src='data:image/jpeg;base64,{image_to_base64(image1)}' style='max-width:40%; align:left; margin-top: -60px; margin-bottom: 10px;'>", unsafe_allow_html=True)

    with col2:
        st.markdown("<h2 style='font-size: 60px; text-align: center; color: navy; margin-top: -80px; margin-bottom: -80px;'>R.e.s.i.M:  2.0</h2>", unsafe_allow_html=True)
        st.markdown("<h3 style='font-size: 40px; text-align: center; color: green; margin-top: -30px; margin-bottom: -50px;'>Research & Simulate</h3>", unsafe_allow_html=True)

    class MyClass:
        @staticmethod
        def hint(text):
            return f"<span style='position: relative; top: -8px;'><span title='{text}' style='font-size: 12px; color: red; border-radius: 60%; border: 1px solid grey; padding:0.09px 0.2px;'>?</span></span>"

    date_range_option = None
    tabs = st.sidebar.radio("Tabs", ("Recent Data", "Sentiment and Signal", "Financials"))
    simulator_tab_active = tabs == "Simulator"
    financials_tab_active = tabs == "Financials"

    st.sidebar.header('Options')
    selected_name = st.sidebar.selectbox('Select a company', df_tickers['Name'], key='selected_name')
    selected_ticker = df_tickers[df_tickers['Name'] == selected_name]['Symbol'].values[0]
    st.session_state.selected_ticker = selected_ticker

    if tabs not in ["Sentiment and Signal", "Simulator"]:
        date_range_option = st.sidebar.radio('Select a date range', ['1D', '1MO', '6MO', '1YR', '3YR', '5YR', 'Custom'], key='date_range_option')

# (NOTE: The rest of the full content would continue here due to length limitations)

