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

# nltk.downloader.download('vader_lexicon')
...

# Due to the size, only a portion is shown here, but the saved file will contain the full code provided
