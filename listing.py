import pandas as pd
import yfinance as yf
import streamlit as st
from datetime import datetime, timedelta

# Define a function to create hint text
def hint(text):
    return f"<span title='{text}'><span style='font-size: 18px; top: -25px; color: red; border-radius: 50%; border: 2px solid grey; padding: 0.5px 8px;'>?</span></span>"

def analyze_stock_data():
    # Load data from the CSV file
    data_df = pd.read_csv('tickers.csv')

    # Define date ranges
    today = datetime.today().date()
    three_months_ago = today - timedelta(days=90)
    six_months_ago = today - timedelta(days=180)
    one_year_ago = today - timedelta(days=365)
    three_years_ago = today - timedelta(days=3 * 365)
    since_2020_date = datetime(2020, 3, 16).date()

    # Function to calculate price changes
    def calculate_price_changes(symbol, end_date):
        try:
            stock_data = yf.download(symbol, start=since_2020_date, end=end_date)
            if len(stock_data) > 0:
                start_price = stock_data['Adj Close'].iloc[0]
                end_price = stock_data['Adj Close'].iloc[-1]
                current_price = stock_data['Adj Close'].iloc[-1]
                since_2020_change = ((end_price - start_price) / start_price) * 100

                three_months_ago_price = yf.download(symbol, start=three_months_ago, end=end_date)['Adj Close'].iloc[0]
                six_months_ago_price = yf.download(symbol, start=six_months_ago, end=end_date)['Adj Close'].iloc[0]
                one_year_ago_price = yf.download(symbol, start=one_year_ago, end=end_date)['Adj Close'].iloc[0]
                three_years_ago_price = yf.download(symbol, start=three_years_ago, end=end_date)['Adj Close'].iloc[0]

                # Determine the category based on since_2020_change
                if since_2020_change <= -40:
                    category = "<= -40%"
                elif since_2020_change <= -20:
                    category = "-40% to -20%"
                elif since_2020_change <= -10:
                    category = "-20% to -10%"
                elif since_2020_change < 0:
                    category = "-10% to 0"
                elif since_2020_change == 0:
                    category = "0"
                elif since_2020_change < 10:
                    category = "0 to 10%"
                elif since_2020_change < 20:
                    category = "10% to 20%"
                else:
                    category = "> 20%"

                return symbol, current_price, since_2020_change, category, three_months_ago_price, six_months_ago_price, one_year_ago_price, three_years_ago_price
            else:
                return None, None, None, None, None, None, None, None
        except Exception as e:
            return None, None, None, None, None, None, None, None

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

    # Streamlit app
    hint_text = hint("This will allow you to select sectors and check the change in stock value between 2020 and the current date. Allows users to see what was the level of drop during the pandemic and how much it has recovered.")
    st.markdown(f'<div class="title-container" style="margin-top: -1px; "><h2 style="color: navy; font-size: 30px;">Custom Analysis {hint_text}</h2></div>',
                unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1.8, 0.9, 3])

    with col1:
        st.write('Enter the end date for analysis:')
        st.write('<span style="color: red; font-size: 20px;">Warning! Data download can take a long time.</span>', unsafe_allow_html=True)
        end_date = st.date_input('End Date', today)

    with col3:
        st.write('<span style="font-size: 20px; color: navy;">Select up to 5 sectors:</span>', unsafe_allow_html=True)
        selected_sectors = st.multiselect('Sectors', data_df['Sector'].unique(), [], key='sectors')

        if len(selected_sectors) == 0:
            st.write('<span style="font-size: 20px; color: red;">Please select one or more sectors- Max 5.</span>', unsafe_allow_html=True)
        elif len(selected_sectors) > 5:
            st.write('<span style="font-size: 20px; color: red;">Sorry! Only 5 sectors are allowed for selection. Please adjust your selections.</span>', unsafe_allow_html=True)
        else:
            confirmation = st.radio("Select an option:", ("No", "Yes"))
            if confirmation == "Yes":
                if st.button("Run Analysis"):
                    # Show the analysis results
                    st.write('Analysis Results:')
                    result = []
                    lower_than_march_2020_df = []
                    progress_bar = st.progress(0)
                    progress_text = st.empty()
                    num_symbols = len(data_df)
                    for index, row in data_df.iterrows():
                        if not selected_sectors or row['Sector'] in selected_sectors:
                            symbol, current_price, since_2020_change, category, three_months_ago_price, six_months_ago_price, one_year_ago_price, three_years_ago_price = calculate_price_changes(row['Symbol'], end_date)
                            if symbol is not None:
                                result.append([row['Name'], row['Symbol'], row['Sector'], round(current_price, 2), round(since_2020_change, 2), category, round(three_months_ago_price, 2), round(six_months_ago_price, 2), round(one_year_ago_price, 2), round(three_years_ago_price, 2)])
                                if since_2020_change < 0:
                                    lower_than_march_2020_df.append([row['Name'], row['Symbol'], row['Sector'], round(current_price, 2), round(since_2020_change, 2), category, round(three_months_ago_price, 2), round(six_months_ago_price, 2), round(one_year_ago_price, 2), round(three_years_ago_price, 2)])
                        progress_percent = (index + 1) / num_symbols
                        progress_bar.progress(int(progress_percent * 100))
                        progress_text.text(f'Processing {index + 1} of {num_symbols} symbols ({int(progress_percent * 100)}%)')
                    result_df = pd.DataFrame(result, columns=['Name', 'Symbol', 'Sector', 'Current Price', 'vs Mar20', ' % (Since-Mar20)', '3MO', '6MO', '1Y', '3Y'])
                    st.markdown("""
                        <style>
                        table td, table th {
                            font-size: 16px;
                            color: navy;
                        }
                        </style>
                        """,
                        unsafe_allow_html=True)
                    st.write('Analysis Results:')
                    st.dataframe(result_df)
                    if lower_than_march_2020_df:
                        lower_than_march_2020_df = pd.DataFrame(lower_than_march_2020_df, columns=['Name', 'Symbol', 'Sector', 'Current Price', 'vs Mar20', ' % (Since-Mar20)', '3MO', '6MO', '1Y', '3Y'])
                        st.write('Stocks with Negative Since 2020 Change:')
                        st.dataframe(lower_than_march_2020_df)
                        lower_than_march_2020_df.to_csv('stocks_with_negative_since_2020_change.csv', index=False)
                    else:
                        st.write('No stocks found with negative Since 2020 Change.')
            else:
                ""

if __name__ == "__main__":
    analyze_stock_data()
