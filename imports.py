import streamlit as st
import altair as alt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
import yahoo_fin.stock_info as si
import plotly.express as px
import plotly.graph_objs as go
import json
import base64
import tqdm
import io
import certifi
import locale
import warnings
import requests
import re
import tweepy
import time
import config
import nltk
import xlsxwriter
import uuid
import datetime as dt
from pathlib import Path
from pandas_datareader import data as pdr
# Note: Using 'ta' library (not pandas_ta) - these are different libraries
# The 'ta' library has the structure: ta.trend, ta.momentum, ta.volatility
from ta.trend import MACD
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands
from ta import add_all_ta_features
from jinja2 import Environment, select_autoescape, FileSystemLoader
from pytz import timezone
from pandas.tseries.offsets import BDay
from datetime import datetime, timedelta, date
from dateutil.parser import parse
from scipy.stats import iqr
from plotly.subplots import make_subplots
from urllib.request import urlopen
from typing import Dict
from matplotlib.backends.backend_agg import FigureCanvasAgg
from streamlit import components
from millify import millify
from yahoo_fin import options, news
from PIL import Image
from bs4 import BeautifulSoup
from xlsxwriter import workbook
from functions import (
    apply_custom_css, custom_css, clear_multi, get_color, get_float_value, 
    get_info, get_stock_industry, color_cells, color_tiers, hint, 
    generate_charts, create_download_link, get_news_yahoo, score_news,
    to_excel, simulate_future_value, display_stock_info, get_trade_open, 
    get_table_download_link, display_current_price, get_stock_info, 
    get_last_price, calculate_stock_sentiment
)
from stock_utils import display_stock_info, display_company_description

