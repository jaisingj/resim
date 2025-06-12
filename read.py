import streamlit as st
st.set_page_config(layout="wide")
from imports import *
import pandas as pd
import stock_utils
import numpy as np
#import yahoo_fin as yf
import datetime as dt
import requests
import pytz
from PIL import Image
from io import BytesIO
import base64
import os
import plotly.graph_objects as go
from simulator import stock_simulation
#from analyze_trend import calculate_buy_sell_signals, create_fig2_plot
from app import analyze_sentiment
from llama import run_llama_chat
from listing import analyze_stock_data
from finfo import financial_dashboard_function
from functions import generate_charts
from theme import run_sector_returns
from yahoo_fin import news
from fmp_helper import fetch_stock_history_fmp

api_key = st.secrets["fmp"]["api_key"]

# Check if 'selected_ticker' exists in session state, and initialize it if not
if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = None  # You can set the initial value to None or any other suitable value

#nltk.downloader.download('vader_lexicon')

hint_text = ""

# Add a sidebar with a radio button selection for navigation
page = st.sidebar.radio("Choose one", ['Analysis', 'ChatBot','Custom Listings','Sectors','FAQ'])




def hint(text):
    return f"<span title='{text}'><span style='font-size: 16px; color: red; border-radius: 50%; border: 1px solid grey; padding: 0.5px 8px;'>?</span></span>"

upload_option_radio = ""

# Depending on the selection, display different pages
if page == 'Analysis':
    # Apply custom CSS styles
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

    with col3:
        pass

    class MyClass:
        @staticmethod
        def hint(text):
            return f"<span style='position: relative; top: -8px;'><span title='{text}' style='font-size: 12px; color: red; border-radius: 60%; border: 1px solid grey; padding:0.09px 0.2px;'>?</span></span>"

    date_range_option = None

    tabs = st.sidebar.radio("Tabs", ("Recent Data", "Sentiment and Signal", "Financials"))

    simulator_tab_active = tabs == "Simulator"
    financials_tab_active = tabs == "Financials"

    # Display the company selection options regardless of the selected tab
    st.sidebar.header('Options')
    selected_name = st.sidebar.selectbox('Select a company', df_tickers['Name'], key='selected_name')
    selected_ticker = df_tickers[df_tickers['Name'] == selected_name]['Symbol'].values[0]
    st.session_state.selected_ticker = selected_ticker


     # Only display the date range option if neither 'Sentiment and Signal' nor 'Simulator' tabs are selected
    if tabs not in ["Sentiment and Signal", "Simulator"]:
        date_range_option = st.sidebar.radio('Select a date range', ['1D', '1MO', '6MO', '1YR', '3YR','5YR', 'Custom'], key='date_range_option')

    today = pd.Timestamp.now(tz=pytz.timezone('US/Eastern')).normalize()  # Get today's date with timezone

    # Initialize the interval
    #interval = '1d'  # Default interval for non-1D options

    # Calculate start and end dates based on the date range option selected
    today = pd.Timestamp.today()

    interval = '1d'  # default fallback

    if date_range_option == '1D':
        start_date = pd.Timestamp.today()
        end_date = start_date
        interval = '1min'
    elif date_range_option == 'Custom':
        start_date = st.sidebar.date_input("Start date", pd.Timestamp.today() - pd.Timedelta(days=30), key='start_date')
        end_date = st.sidebar.date_input("End date", pd.Timestamp.today(), key='end_date')
        interval = '1d'  # Set something explicitly here too
        
    else:
        start_date = today - pd.Timedelta(days=5)
    end_date = today
    if date_range_option == '5D':
        pass
    elif date_range_option == '1MO':
        start_date = today - pd.Timedelta(days=30)
    elif date_range_option == '6MO':
        start_date = today - pd.Timedelta(days=180)
    elif date_range_option == '1YR':
        start_date = today - pd.Timedelta(days=365)
    elif date_range_option == '3YR':
        start_date = today - pd.Timedelta(days=1095)
    elif date_range_option == '5YR':
        start_date = today - pd.Timedelta(days=1825)


    elif date_range_option == 'Custom':
        start_date = st.sidebar.date_input("Start date", today - pd.Timedelta(days=30), key='start_date')
        end_date = st.sidebar.date_input("End date", today, key='end_date')
    else:
        # Default to '1MO' if something goes wrong
        start_date = today - pd.Timedelta(days=365)
        end_date = today

    # Now safe to define cache_key
    cache_key = f"{selected_ticker}_{date_range_option}_{interval}"

 
    if tabs == "Recent Data":
        hint_text = hint("This page shows you all the recent available data and various trends. Based on the Yfinance specifications data is only available in intervals of 1D, 5D, 1WK, 1MO and 3MO (1MO only for MACD)")

        st.markdown(f'<div class="title-container" style="margin-top: -4px;"><h3 style="color: navy; font-size: 28px;">Recent Data - {selected_name} {hint_text}</h3></div>', unsafe_allow_html=True)


        def update_chart(selected_ticker, start_date, end_date):
            ticker = yf.Ticker(selected_ticker)
            ticker_history = fetch_stock_history_fmp(selected_ticker, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))

        formatted_start_date = start_date.strftime("%B %d, %Y")
        formatted_end_date = end_date.strftime("%B %d, %Y")

        # Check if end date is after begin date otherwise present an error message
        if start_date < end_date:
            st.sidebar.markdown(f'<div style="background-color: #CEDDF1; border: 0.4px solid navy; border-radius: 2px; padding: 10px; margin-bottom: 20px;">Selected Date range:<br><br><strong>{formatted_start_date}</strong><br><br><strong>{formatted_end_date}</strong></div>', unsafe_allow_html=True,)
        else:
            st.sidebar.error('Error: End date must fall after start date.')

        symbols = pd.read_csv('tickers.csv')['Symbol'].tolist()
        recent_data = None

        if tabs == "Recent Data":

            with st.container():
                try:
                    start_month_year = start_date.strftime("%Y-%b")
                    end_month_year = end_date.strftime("%Y-%b")
                    start_date_fmt = pd.to_datetime(start_month_year).replace(day=1).strftime("%Y-%m-%d")
                    end_date_fmt = pd.to_datetime(end_month_year).replace(day=pd.to_datetime(end_date).day).strftime("%Y-%m-%d")

                    ticker = yf.Ticker(selected_ticker)
                    ticker_history = ticker.history(start=start_date_fmt, end=end_date_fmt)

                    if ticker_history is None or ticker_history.empty:
                        st.warning("No historical data found for the selected ticker and date range.")
                  
                except Exception as e:
                    st.error(f"Failed to fetch ticker history: {e}")


                st.markdown("""
                    <style>
                    .title-container {
                        border-top: 1.0px solid #082C9C;  
                        border-bottom: 1.0px solid #082C9C; 
                        padding: 0.1px;
                        background-color: #CEDDF1;
                        text-align: center;
                        margin-top: 12px; margin-bottom: 3px
                    }
                    </style>
                    """, unsafe_allow_html=True)

        display_stock_info()
        generate_charts(start_date, end_date, selected_ticker, date_range_option)
            
        if __name__ == '__main__':

            def main():              
                
                # Today's date
                today_date = datetime.now().strftime("%b %d %Y")
                
                # Assuming selected_ticker is defined elsewhere in the code
                selected_ticker = st.session_state.selected_ticker  # Default to 'AAPL' if not set
                #selected_name = st.session_state.selected_ticker  # Default to 'AAPL' if not set
                
                # Displaying company description
                col1, col2, col3 = st.columns([0.5, 0.1, 0.6])

                with col1:
                    # Fetch and display company description
                    st.markdown(f'<h3 style="color: navy; font-size: 30px; margin-top: -10px;">Company Description - {st.session_state.selected_name}</h3>', unsafe_allow_html=True)
                    display_company_description(selected_ticker)
                    #st.write(f'<div style="font-size: 20px;">{description}</div>', unsafe_allow_html=True)

                with col3:
                    today_date = datetime.now().strftime("%b %d %Y")
                    #st.write(f'<div style="font-size: 35px; color:navy">Latest News for {st.session_state.selected_name} ({today_date})</div>', unsafe_allow_html=True)
                    st.markdown(f'<h3 style="color: navy; font-size: 30px; margin-top: -10px;">Latest News for {st.session_state.selected_name} ({today_date})</h3>', unsafe_allow_html=True)

    
                    stock_news_headlines = news.get_yf_rss(selected_ticker)

                    for item in stock_news_headlines[:5]:
                        st.subheader(item['title'])
                        st.write(item['summary'])
                        st.markdown(f"[Read more]({item['link']})", unsafe_allow_html=True)





 
            if __name__ == "__main__":
                main()


#****************** Tab 2: Sentiment and Signal**************************************

    elif tabs == "Sentiment and Signal":
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
            </style>
            """, unsafe_allow_html=True)

        hint_text = hint("This section allows you to view the current sentiment for a company based on news snippets and tools like NLTK, VADER Sentiment analysis which assigns a score to the article. There is also an overall compound score which looks at the Min and Max of the scores for news on the same day and assigns a potential buy or sale signal. Read the FAQ for more details.")
        st.markdown(
            f'<div class="title-container" style="margin-top: -2px;"><h2 style="color: navy; font-size: 30px;">Sentiment and Trade Signal  {hint_text}</h2></div>',
            unsafe_allow_html=True)

        def get_jsonparsed_data(url):
            response = requests.get(url)
            if response.status_code == 200:
                response_data = response.json()[:5]  # Get the 5 most recent data.
                results = []
                for data in response_data:
                    result = {
                        "Year": int(data.get('date', 'N/A')[:4]),  # Extract year from the date
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

  
        #st.markdown('<h2 style="font-size: 30px;">Financial Information and News ' + hint(
            #"Financial Info and News articles about the selected Symbol!") + '</h2>', unsafe_allow_html=True)

        # Creating a gap
        st.markdown("<br>", unsafe_allow_html=True)
        # Creating a gap
        st.markdown("<br>", unsafe_allow_html=True)

        url = f"https://financialmodelingprep.com/api/v3/income-statement/{selected_ticker}?period=annual&limit=5&apikey=4c765c89222f1c67f8a20831ed03265f"
        data = get_jsonparsed_data(url)

        if data:
            df = pd.DataFrame(data)
            df = df.sort_values('Year')
            df["Y/Y"] = df["Net Income"].pct_change().fillna(0) * 100
            df['Y/Y'] = df['Y/Y'].replace({0: ''})
            df["Y/Y"] = df["Y/Y"].apply(
                lambda x: f'<span style="color: {"red" if x < 0 else "green"}">{x:.2f}%</span>' if x != '' else '')
            numerical_columns = df.select_dtypes(include=[np.number]).columns.tolist()
            df[numerical_columns] = df[numerical_columns].round(2)

            bar_chart_data = df[["Year", "Revenue", "Net Income"]].copy()
            bar_chart_data.set_index("Year", inplace=True)

            plt.figure(figsize=(4, 3))
            ax = bar_chart_data.plot(kind='bar', edgecolor='none')
            plt.xticks(rotation=0, fontsize='small')
            plt.title('Revenue & Net Income (USD)')
            plt.ylabel('Amount (in billions)')
            plt.xlabel('Year')

            for spine in ax.spines.values():
                spine.set_visible(False)

  
            col1, col2 = st.columns([0.4,0.35])
            st.session_state.selected_ticker = selected_ticker

   
            with col1:
                analyze_sentiment(st.session_state.selected_ticker)

            

            # Define news_table by calling get_news_yahoo or any other method
            #news_table = get_news_yahoo(selected_ticker)  # You need to adapt this to your code


            selected_ticker = st.session_state.selected_ticker

            #with col2:
                #st.markdown("<h4 style='color: navy; text-align: center;'>90 day Buy/Sell Signal: {}</h4>".format(st.session_state.selected_name), unsafe_allow_html=True)
                #display_fig2(st.session_state.selected_ticker)

#****************** Tab 2: End of Tab 2 **************************************

#****************** Tab 3: Simulator******************************************





    elif tabs == "Financials":
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
            </style>
            """, unsafe_allow_html=True)
         #Create a title for the chart with the specified style
        #hint_text = hint("This section allows you to simulate investment strategies for what-if scenarios using historical data and Future potential Portfolio value based on investments you plan to make if the stock moved up or down by a certain percentage point.")
        st.markdown(
            f'<div class="title-container" style="margin-top: -2px;"><h2 style="color: navy; font-size: 30px;">Financials{hint_text}</h2></div>',
            unsafe_allow_html=True)

        if financials_tab_active:
        # Only run financial_dashboard_function when the Financials tab is active
            financial_dashboard_function(selected_name)




elif page == 'FAQ':
    st.markdown('<h2 style="color: navy; font-size: 28px;">Frequently Asked Questions</h2>', unsafe_allow_html=True)
    st.markdown('<div class="title-container" style="margin-top: -4px;"></div>', unsafe_allow_html=True)

    st.markdown('<h3 style="color: navy;">1. What is R.e.s.i.M?</h3>', 
unsafe_allow_html=True)
    st.markdown("<h5 <p> Research and Simulation. It is a free web application that uses Streamlit to execute python code which provides financial information and Sentiment analysis using the NLTK tool kit and VADER ( Valence Aware Dictionary for Sentiment Reasoning) model for publicly traded companies. The main goal was to test these tools and also demonstrate that ChatGPT is not just some tool for exploring creative writing, generating ideas and merely interacting with AI. It allowed me to accelerate designing this whole application within 90 days. This started as a hobby project during the lockdown to avoid the meme stock frenzy and design a custom dashboard with key metrics and simulation capabilities before making investment decisions. I put it on the shelf since some of the customization and complex functions such as news scraping, VADER would need extensive coding and debugging , ChatGPT API allowed me to do all of that along with integrating the Sentiment analysis much faster than I envisioned.</p> </h5>", unsafe_allow_html=True)

    st.markdown("<h5 <p> The app helps me make informed decisions by analyzing historical stock data, Sentiment Analysis of news articles, and a Stock Simulator to determine the potential value of investments based on expected price changes I can enter manually to determine both Gains and Losses. The application does not have live stock price updates. It is aimed purely at research and analysis.</p> </h5>", unsafe_allow_html=True)

    st.markdown('<h3 style="color: navy;">2. How do I use R.e.s.i.M?</h3>', unsafe_allow_html=True)
    st.markdown("<h5 <p>On the 'Analysis' tab, select a company from the dropdown menu and specify the date range and interval for historical stock data. You will also see a few key metrics such as current price, P/E ratio etc. The Recent Data tab shows 4 charts, A candlestick price chart with the S&P 500 index, A 10 day and 20 Day Moving average chart with Buy/Sell Signals, MACD and RSI charts. The Sentiment analysis tab shows a chart depicting recent sentiment compound scores calculated using VADER which uses news articles about the selected company on Yahoo Finance. Stock simulation allows testing  both historical what-if scenarios and investment future value.</p> </h5>", unsafe_allow_html=True)


    st.markdown('<h3 style="color: navy;">3. Is R.e.s.i.M free to use?</h3>', unsafe_allow_html=True)
    st.markdown("<h5 <p>Yes, R.e.s.i.M is free to use. It is provided as an educational tool to help users explore financial and sentiment analysis for publicly traded companies. Currently I am not accepting customization requests or providing technical support for issues that are not related directly to the app. I will continue to refine the app based on feedback and personal use. There are many articles, blogs and white papers users can search online to get more detail on the ideas I have talked about. </p> </h5>", unsafe_allow_html=True)



    st.markdown('<h3 style="color: navy;">4. Can I upload my own personal list of companies and use this app ?</h3>', unsafe_allow_html=True)
    st.markdown("<h5 <p>Yes, you can use the Upload CSV option in the Simulator tab and upload your own custom list. The list must have two columns. 1. Symbol and 2 Name in title case. The format should be csv and it does not require a specific name. For e.g. If I have 5 stocks to research, I can add them and call the file myfile.csv</p> </h5>", unsafe_allow_html=True)



    st.markdown('<h3 style="color: navy;">5. Can I use this for real trading?</h3>', unsafe_allow_html=True)
    st.markdown("<h5 <p> No, R.e.s.i.M is for research and simulation purposes only. It does not support real time trading or live price updates. It does not provide investment advice or make recommendations of any kind.  Users must consult with a financial advisor before making investment decisions that may result in a financial loss. The buy and trade signals are based on  moving averages and can be impacted by sudden changes in the financial health of a company, the overall market sensitivity and any external factors such as political instability or unforeseen events.   </p> </h5>", unsafe_allow_html=True)


    st.markdown('<h3 style="color: navy;">6. Can I download my Simulations?</h3>', unsafe_allow_html=True)
    st.markdown("<h5 <p>Yes, you can export them to a excel spreadsheet and save them for future reference. If you close the browser, your simulation summaries will not be saved. The app does not download historical prices for each symbol in the database for the time period selected. The databased has 5K or more companies and downloading that much data can take hours and also use up the daily limit allowed by Yahoo Finance since it is open source.</p> </h5>", unsafe_allow_html=True)

    st.markdown('<h3 style="color: navy;">7. How do I run a Simulation?</h3>', unsafe_allow_html=True)
    st.markdown("<h5 <p> You can perform a historical simulation titled as Select from List or run a hypothetical simulation which is titled as Simulate Future Value. For the historical simulation you will need to enter a Buy date, Sell date and an Investment amount you would have invested. Click on the Simulate button and the application will take the prices for the two dates and you can see the potential earnings or loss you would have made. Default buy date is 1 year from the current date. Click on the buy date field to select a custom date. You can add more than one company name before clicking on the Simulate button  </p> </h5>", unsafe_allow_html=True)

    st.markdown("<h5 <p> For the Simulation of future value of a portfolio, select the company name and input a dollar amount you want to invest and a percentage increase or decrease you want to test to see the Gain or Loss you will make if the stock was to appreciate in value or drop in value. Default investment amount is $100, you can add the amount you wish to invest by typing it in or selecting the + sign. You can save both the simulations by downloading them as an excel output.  </p> </h5>", unsafe_allow_html=True)


    st.markdown('<h3 style="color: navy;">8. How many Simulations can I run?</h3>', unsafe_allow_html=True)
    st.markdown("<h5 <p>R.e.s.i.M is a free app and uses open source packages such as yfinance and yahoo_fin. There is a limit of how many requests for data you can make per day, if the limit is surpassed then the application may be unable to run or fetch data till the next business day. There are other applications which are paid apps and allow unlimited cycles of fetching data.</p> </h5>", unsafe_allow_html=True)


    st.markdown('<h3 style="color: navy;">9. How is the Sentiment analysis performed ?</h3>', unsafe_allow_html=True)
    st.markdown("<h5 <p> R.e.s.i.M uses the VADER (Valence Aware Dictionary and Sentiment Reasoner) sentiment analysis tool to analyze the sentiment of news articles. VADER assigns a sentiment score (positive, negative, or neutral) to each article based on the text's content.</p> </h5>", unsafe_allow_html=True)


    st.markdown('<h3 style="color: navy;">10. What is the difference between the 90 day Signal and Sentiment score chart and table?</h3>', unsafe_allow_html=True)
    st.markdown("<h5 <p> These are based on the analysis of texts in which a positive or negative sentiment is assigned according to the words that a certain phrase or text contains. This analysis combines the use of Natural Language Processing (NLP) and Machine Learning to assign scores to publications, also, these scores are weighed according to the number of times it appears. VADER collects and scores negative, neutral, and positive words and features (and accounts for factors like negation along the way). The “neg”, “neu”, and “pos” values describe the fraction of weighted scores that fall into each category. VADER also sums all weighted scores to calculate a “compound” value normalized between -1 and 1; this value attempts to describe the overall affect of the entire text from strongly negative (-1) to strongly positive (1). </p> </h5>", unsafe_allow_html=True)

    st.markdown('<h3 style="color: navy;">11. How is the Min Score and Max Score calculated?</h3>', unsafe_allow_html=True)
    st.markdown("<h5 <p> We have several news items per date, for which VADER assigns an individual compound score, we then assign new score based on the minimum and maximum of each of the dates and then use the sentimental analysis score as a signal to buy or sell a stock according to an optional threshold, in this case 0.3 will be used as a reference point to good or bad news. </p> </h5>", unsafe_allow_html=True)


    st.markdown('<h3 style="color: navy;">12.How are the Price Trend with Buy/Sell Signals calculated in the main app?</h3>', unsafe_allow_html=True)
    st.markdown("<h5 <p>Moving averages at 10 and 20 days, in the case the 10-day moving average crosses the 20-day moving average, above it will mean that the price will fall and the stock must be sold, otherwise, it will be a signal that the stock must be bought.</p> </h5>", unsafe_allow_html=True)

    st.markdown('<h3 style="color: navy;">13.What are RSI and MACD?</h3>', unsafe_allow_html=True)
    st.markdown("<h5 <p>The RSI aims to indicate whether a market is considered to be overbought or oversold in relation to recent price levels. The RSI calculates average price gains and losses over a given period of time; the default time period is 14 periods. RSI values are plotted on a scale from 0 to 100. Values over 70 are considered indicative of a market being overbought in relation to recent price levels, and values under 30 are indicative of a market that is oversold. On a more general level, readings above 50 are interpreted as bullish, and readings below 50 are interpreted as bearish.</p> </h5>", unsafe_allow_html=True)

    st.markdown("<h5 <p> The MACD(Moving Average Convergence/Divergence) indicator is a momentum oscillator primarily used to trade trends. Although it is an oscillator, it is not typically used to identify over bought or oversold conditions. It appears on the chart as two lines which oscillate without boundaries. The crossover of the two lines give trading signals similar to a two moving average system. MACD crossing above zero is considered bullish, while crossing below zero is bearish. Secondly, when MACD turns up from below zero it is considered bullish. When it turns down from above zero it is considered bearish.</p> </h5>",unsafe_allow_html=True)

    st.markdown('<h3 style="color: navy;">14.Is the app and code available for download?</h3>', unsafe_allow_html=True)
    st.markdown("<h5 <p>The app for now can only be run via the streamlit web link. I will be looking for feedback on usage and issues and then customize based on the most common ask. I am using my own private paid API key to get some data. In the future I may release a paid version which will allow me to make the application provide live data as well as cover the API key cost which will allow larger amount of requests.</p> </h5>", unsafe_allow_html=True)

    st.markdown('<h3 style="color: navy;">15.What is the Custom CSV option?</h3>', unsafe_allow_html=True)
    st.markdown("<h5 <p>My default file has ~8000 companies, but if you want to only research for e.g. 20 companies you are currently holding in your portfolio or have your own list you want to reference for analysis, you can upload it to the app. Note: The app does not save your file or store it on the cloud or GitHub repository. Once you close the app or the browser, the file is deleted automatically.</p> </h5>", unsafe_allow_html=True)

    st.markdown('<h3 style="color: navy;">16.My trading app allows me to see a lot of this information and there are other similar apps there?</h3>', unsafe_allow_html=True)
    st.markdown("<h5 <p>Yes, but the trading apps determine the layout of the information and how you can perform a simulation. Some of them give sentiment based scores but I wanted to have a custom app and the ability to add or remove features myself and also run the application offline. </p> </h5>", unsafe_allow_html=True)


elif page == 'ChatBot':
    run_llama_chat()

elif page == 'Custom Listings':
    analyze_stock_data()

elif page == 'Sectors':
    run_sector_returns()




#****************** FAQ Tab: End of FAQ Tab ******************************************
 
#****************** End of all Tabs ******************************************
