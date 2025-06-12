import streamlit as st
import pandas as pd
import yfinance as yf
import datetime
import base64
import time
from functions import simulate_future_value, get_table_download_link, simulate_portfolio

company_name = ""
symbol = ""
company_sec = ""  # Define company_sec at the top of your script




# Define CSS styles for the button
button_style = '''
    <style>
    .stButton button {
        background-color: navy;
        color: white;
    }
    .stButton button:hover {
        background-color: darkblue;
    }
    </style>
'''

# Apply custom HTML styles to the radio button label
choose_csv_html = '''
    <style>
    .csv-radio-label {
        font-size: 20px;
        color: navy !important;
    }
    </style>
'''

def stock_simulation():
    start_dates = {}
    end_dates = {}
    amounts = {}
    one_year_ago = datetime.date.today() - datetime.timedelta(days=365)

    ticker_df = None

    col1, col2, col3, col4 = st.columns([0.5, 0.5, 0.6, 0.5])

    with col1:
        # Use markdown for "Choose CSV Source"
        choose_csv_markdown = '<div style="font-size:20px; color:navy; margin-top: 10px; margin-bottom: -70px; padding-left:10px;">1. Choose CSV Source</div>'
        st.markdown(choose_csv_markdown, unsafe_allow_html=True)

    #with col2:
        # Display the radio button for CSV source selection
        st.markdown('<div style="padding-right:30px;">', unsafe_allow_html=True)
        use_default_csv = st.radio('', ['Default (tickers.csv)', 'Custom (Upload CSV)'])
        st.markdown('</div>', unsafe_allow_html=True)

        if use_default_csv == 'Default (tickers.csv)':
            ticker_df = pd.read_csv('tickers.csv')
        else:
            # Allow the user to upload a custom CSV file
            custom_csv_file = st.file_uploader('Upload a custom CSV file', type=['csv'])
            if custom_csv_file is not None:
                ticker_df = pd.read_csv(custom_csv_file)

    with col3:
    # Use markdown to display "Choose an option:"
        col3.markdown('<div style="font-size: 20px; color:navy; margin-top: 10px; margin-bottom: -30px;"> 2. Choose an option:</div>', unsafe_allow_html=True)
    
    # Display the radio buttons for "2. Choose an option" directly below the label
        option = col3.radio('', ['Simulate Historical Prices', 'Simulate Future Growth %', 'Custom Prices'])
    # Check if ticker_df is still None and handle the case where it's not available
    if ticker_df is None:
        st.error("Please select a CSV source.")
        return

    ticker_df = pd.read_csv('tickers.csv')
    tickers = ticker_df['Symbol'].tolist()
    names = ticker_df['Name'].tolist()
    sec = ticker_df['Sector'].tolist()
    ind = ticker_df['Industry'].tolist()
    selected_symbols = []
    symbol_target_percentages = {}
    custom_investment_amounts = {}  # Store custom investment amounts here
    simulate_button = False
    selected_names = []

    col4, col5, col6 = st.columns([0.1, 0.4, 0.3])

    with col5:
        selected_names_label = "3. Select One or more Company:"
        selected_names_markdown = f'<div style="font-size: 20px; color: navy; margin-top: 20px; margin-bottom: -20px;">{selected_names_label}</div>'
        st.markdown(selected_names_markdown, unsafe_allow_html=True)

        if option == 'Select from list':
            selected_names = st.multiselect('', names)
        elif option == 'Simulate Future Value':
            selected_symbols = st.multiselect('', names)

        custom_investment_amounts = {}
        symbol_target_percentages = {}

    # Create two columns with equal width (you can adjust the widths as needed)
    col1, col2 = st.columns([0.5,0.5])

    # Iterate through selected symbols to create input fields side by side
    for symbol in selected_symbols:
        container = st.container()
        with col1:
            custom_investment_amounts[symbol] = st.number_input(
                f"",
                min_value=100.0, step=500.0,
                key=f"custom_investment_{symbol}"
            )

            st.markdown(f"<span style='font-size: 20px; margin-top: 20px; margin-bottom: -20px;'>Investment Amount for {symbol}</span>", unsafe_allow_html=True)

        with col2:
            st.markdown("""
                <style>
                /* Change the slider handle color to blue */
                .stSlider {
                    margin-top: -30px !important;
                }
                /* Change the slider track color to blue */
                .stSlider .stSlider-track {
                    background-color: blue !important;
                }

                .stSlider .stSlider-label {
                    font-size: 40px !important;
                }
                /* Set color for -100 value to red */
                .stSlider .stSlider-label[title='-100.0'] {
                    color: red !important;
                }
               /* Set color for 100 value to green */
                .stSlider .stSlider-label[title='100.0'] {
                    color: green !important;
                }
                </style>
             """, unsafe_allow_html=True)

            symbol_target_percentages[symbol] = st.slider(
                f"",
                min_value=-500.0, max_value=1000.0, step=0.05, value=0.0,
                key=f"target_percentage_{symbol}"
            )
            st.markdown(f"<span style='font-size: 20px; margin-bottom: -20px;'>Investment Amount for {symbol}</span>", unsafe_allow_html=True)

    with col5:
        # Place the simulate button here
        simulate_button = st.button('Simulate', key='main_simulation_button', help="Simulate the selected companies")

        # Apply the styles using HTML
        st.markdown(button_style, unsafe_allow_html=True)

    if selected_names:
        for name in selected_names:
            ticker = tickers[names.index(name)]
            col1, col2, col3, col4, col5 = st.columns([0.6, 0.5, 0.5, 0.6, 0.5])

            with col1:
                st.markdown(f"<div style='color: black; font-size: 19px;'>{name}</div>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"<div style='color: black; font-size: 20px; margin-bottom: -40px;'>Buy date</div>",
                            unsafe_allow_html=True)
                start_dates[name] = st.date_input("", value=one_year_ago, key=f"start_{name}")
            with col3:
                st.markdown(f"<div style='color: black; font-size: 20px; margin-bottom: -40px;'>Sell date</div>",
                            unsafe_allow_html=True)
                end_dates[name] = st.date_input("", value=None, key=f"end_{name}")
            with col4:
                st.markdown(f"<div style='color: black; font-size: 20px; margin-bottom: -40px;'>Investment($)</div>",
                            unsafe_allow_html=True)
                amounts[name] = st.number_input("", min_value=100.0, step=100.0, key=f"amount_{name}")
            with col5:
                st.markdown('<div style="color: black; font-size: 20px; margin-bottom: -20px;">Trend Chart</div>',
                            unsafe_allow_html=True)
                if st.checkbox(f'', key=f"checkbox_{ticker}"):
                    start_date = start_dates[name]
                    end_date = end_dates[name]
                    chart_data = yf.download(ticker, start=start_date, end=end_date)
                    st.line_chart(chart_data['Close'])

    if option == 'Simulate Future Value' and simulate_button:
        progress_bar = st.progress(0)
        count_text = st.empty()
        future_value_summary = []
        total_symbols = len(selected_symbols)
        for i, symbol in enumerate(selected_symbols, start=1):
            company_name = names[names.index(symbol)]
            # Use the custom investment amount if provided, otherwise use 0 as a default value
            custom_investment = custom_investment_amounts.get(symbol, 0)
            target_percentage_str = str(symbol_target_percentages.get(symbol, 0))  # Get target
            target_percentage = float(target_percentage_str)
            simulation_result = simulate_future_value(symbol, target_percentage, custom_investment)
            if simulation_result:
                future_value_summary.append(simulation_result)

            #progress_percent = (i + 1) / len(selected_symbols)
            #progress_bar.progress(progress_percent)

            progress_percent = i / total_symbols  # Normalize to [0.0, 1.0]
            progress_bar.progress(progress_percent)

            count_text.text(f"Processing {i}/{total_symbols}")
        
        # Display the count of symbols chosen
            #st.text(f"Processing {i}/{total_symbols}")
 

        
        # Sleep for a short duration to allow the progress bar to update (optional)
            time.sleep(0.2)

        if future_value_summary:
            future_value_df = pd.DataFrame(future_value_summary)
            # Update the column name to 'Company Name'
            future_value_df.rename(columns={'Company': 'Company Name'}, inplace=True)
            # Format the relevant columns to use {:.2f}
            future_value_df['Current Price'] = future_value_df['Current Price'].apply(lambda x: "${:.2f}".format(x))
            #future_value_df['Target %'] = future_value_df['Target Percentage'].apply(lambda x: "{:.2f}%".format(x))
            future_value_df['Investment'] = future_value_df['Investment'].apply(lambda x: "${:.2f}".format(x))
            future_value_df['Shares'] = future_value_df['Shares'].apply(lambda x: "{:.2f}".format(x))
            future_value_df['Gains'] = future_value_df['Gains'].apply(lambda x: "${:.2f}".format(x))
            #future_value_df['Target Price'] = future_value_df['Target Share Price'].apply(lambda x: "${:.2f}".format(x))
            future_value_df['Custom Investment'] = future_value_df['Custom Investment'].apply(lambda x: "${:.2f}".format(x))
            future_value_df = future_value_df.drop(columns=['Custom Investment'])

            # Apply formatting to the "Total Gain/Loss" column based on the condition
            def format_total_gain_loss(row):
                total_gain_loss = row['Potential Gain/Loss']
                if total_gain_loss < 0:
                    return f"({abs(total_gain_loss):.2f})"
                else:
                    return f"{total_gain_loss:.2f}"

            future_value_df['Potential Gain/Loss'] = future_value_df.apply(format_total_gain_loss, axis=1)

            # Calculate total investment and total return for future simulation
            total_future_investment = future_value_df['Investment'].str.replace('$', '').str.replace(',', '').astype(float).sum()
            total_future_return = future_value_df['Potential Gain/Loss'].str.replace('$', '').str.replace(',', '').astype(float).sum()
           
           # Calculate total investment and total return for future simulation
            total_future_investment = future_value_df['Investment'].str.replace('$', '').str.replace(',', '').astype(float).sum()
            total_future_return = future_value_df['Potential Gain/Loss'].str.replace('$', '').str.replace(',', '').astype(float).sum()
            total_future_return_percent = (total_future_return-total_future_investment)/(total_future_investment)* 100
            total_investment_color = "red" if total_future_investment < 0 else "green"
            total_return_color = "red" if total_future_return < 0 else "green"
            total_return_percent_color = "red" if total_future_return_percent < 0 else "green"

            # Inject CSS to increase font size of table contents
            st.markdown("""
            <style>
            table td, table th {
                font-size: 20px; color:navy;  /* Adjust font size as desired */
            }
            </style>
            """, unsafe_allow_html=True)

            # Display the table in Streamlit
            st.table(future_value_df)

            totcol1, totcol2, totcol3 = st.columns([0.4, 0.4, 0.6])

            formatted_total_future_investment = '{:,.2f}'.format(total_future_investment)
            formatted_total_future_return = '{:,.2f}'.format(total_future_return)
            formatted_total_future_return_percent = '{:,.2f}'.format(total_future_return_percent)

            with totcol1:
                st.markdown(f"<span style='font-size: 20px; color: {total_investment_color}; font-style: normal;'>Total Investment: ${formatted_total_future_investment}</span>", unsafe_allow_html=True)
            with totcol2:
                st.markdown(f"<span style='font-size: 20px; color: {total_return_percent_color}; font-style: normal;'>Total Gain/Loss: ${formatted_total_future_return}</span>", unsafe_allow_html=True)
            with totcol3:
                st.markdown(f"<span style='font-size: 20px; color: {total_return_percent_color}; font-style: normal;'>Total Potential Return (%): {formatted_total_future_return_percent}%</span>", unsafe_allow_html=True)

           

            st.markdown('<p style="font-size:18px; color:navy">{}</p>'.format(get_table_download_link(future_value_df, 'Download Summary', 'Future_Sim_Summary')), unsafe_allow_html=True)

    if selected_names and simulate_button:
        summary = []
        total_purchase = 0.0
        total_sale = 0.0
        data_downloaded = 0
        skipped_symbols = []

        progress_col1, progress_col2, progress_col3 = st.columns([0.3, 0.9, 0.3])
        with progress_col2:
            progress = st.progress(0)
        progress_text = st.empty()

        for name in selected_names:
            ticker = tickers[names.index(name)]
            data = yf.download(ticker)
            

            if data.empty:
                st.write(f"No data found for {name}. Skipping...")
                skipped_symbols.append(ticker)
                continue

            start_date = data.index[0] if pd.isnull(start_dates[name]) else data.index.asof(datetime.datetime.combine(start_dates[name], datetime.datetime.min.time()))
            end_date = data.index[-1] if pd.isnull(end_dates[name]) else data.index.asof(datetime.datetime.combine(end_dates[name], datetime.datetime.min.time()))
            amount = amounts[name]

            start_price = data.loc[start_date, 'Close']
            end_price = data.loc[end_date, 'Close']
            shares_bought = amount / start_price
            purchase_amount = shares_bought * start_price
            sale_amount = shares_bought * end_price
            profit_percent = ((sale_amount - purchase_amount) / purchase_amount)*100

            # Fetch company_sec and company_ind from ticker_df
            company_sec = sec[names.index(name)]
            company_ind = ind[names.index(name)]



            summary.append({
                'Company': name,
                'Industry': company_ind,
                'Sector': company_sec,
                'Buy Date': start_date.strftime('%b %d, %Y'),
                'Sell Date': end_date.strftime('%b %d, %Y'),
                'Buy Price': "{:.2f}".format(data.loc[start_date, 'Close']),
                'Sell Price': "{:.2f}".format(data.loc[end_date, 'Close']),
                'Shares': "{:.2f}".format(shares_bought),
                'Purchase($)': "{:.2f}".format(purchase_amount),
                'Sale($)': "{:.2f}".format(sale_amount),
                'Return (%)': "{:.2f}".format(profit_percent),
            })

            total_purchase += purchase_amount
            total_sale += sale_amount
            data_downloaded += 1
            progress.progress(data_downloaded / len(selected_names))
            progress_text.text(f"Downloading data for {data_downloaded} of {len(selected_names)} stocks.")

        summary_df = pd.DataFrame(summary)

        st.markdown("""
        <style>
        table td, table th {
            font-size: 18px; color: navy;  /* Adjust font size and color as desired */
        }

        table th {
            background-color: inherit; /* Keep the background color as is */
            color: black; /* Change the font color of column headers to black */
}

        </style>
        """, unsafe_allow_html=True)


        summary_df['Return (%)'] = summary_df['Return (%)'].astype(float)

        st.table(summary_df.style.format({'Return (%)': '{:.2f}'}).apply(
            lambda x: ["color: red" if v < 0 else "color: green" for v in x], subset=['Return (%)']))

        total_return = total_sale - total_purchase
        total_return_percent = (total_return / total_purchase) * 100

        total_investment_color = "red" if total_purchase < 0 else "green"
        total_return_color = "red" if total_return < 0 else "green"
        total_return_percent_color = "red" if total_return_percent < 0 else "green"

        totcol1, totcol2, totcol3 = st.columns([0.4, 0.4, 0.3])



        formatted_total_purchase = '{:,.2f}'.format(total_purchase)
        formatted_total_sale = '{:,.2f}'.format(total_sale)
        formatted_total_return_percent = '{:,.2f}'.format(total_return_percent)

        with totcol1:
            st.markdown(f"<span style='font-size: 20px; color: {total_investment_color}; font-style: normal;'>Total Investment: ${formatted_total_purchase}</span>", unsafe_allow_html=True)
        with totcol2:
            st.markdown(f"<span style='font-size: 20px; color: {total_return_color}; font-style: normal;'>Total Return: ${formatted_total_sale}</span>", unsafe_allow_html=True)
        with totcol3:
            st.markdown(f"<span style='font-size: 20px; color: {total_return_percent_color}; font-style: normal;'>Total Return (%): {formatted_total_return_percent}%</span>", unsafe_allow_html=True)

        if skipped_symbols:
            st.warning(f"Skipped symbols: {', '.join(skipped_symbols)}")

        st.markdown('<p style="font-size:20px; color:navy">{}</p>'.format(get_table_download_link(summary_df, 'Download Summary', 'summary')), unsafe_allow_html=True)

if __name__ == '__main__':
    stock_simulation()
