import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf

# Function to get the last closing price of a stock
def get_closing_price(symbol):
    ticker = yf.Ticker(symbol)
    stock_info = ticker.history(period="1d")
    if not stock_info.empty:
        return stock_info['Close'].iloc[-1]
    else:
        return None  # Return None if no data

# Function to calculate the number of shares, investment, etc.
def calculate_shares(data, investment_amount):
    results = []  # List to store result dictionaries
    min_percentage = 0.50  # Define the minimum percentage threshold
    other_investment = 0.0

    for _, row in data.iterrows():
        symbol = row['Symbol']
        name = row['Name']
        sector = row['Sector']
        percentage_str = row['Percentage']

        # Convert percentage to float
        percentage = float(percentage_str.replace('%', '')) if '%' in percentage_str else float(percentage_str)

        if percentage < min_percentage:
            # If the percentage is below the threshold, add the investment to the "Other" category
            other_investment += round(investment_amount * (percentage / 100), 2)
        else:
            # Calculate investment and shares for other symbols
            amount_for_symbol = round(investment_amount * (percentage / 100), 2)
            last_close_price = get_closing_price(symbol)
            if last_close_price is not None:
                shares = round(amount_for_symbol / last_close_price, 2)
            else:
                last_close_price = 'Data not available'
                shares = 'Data not available'

            result = {
                'Symbol': symbol,
                'Name': name,
                'Sector': sector,
                'Percentage': f"{percentage:.2f}%",
                'Last Close Price': f"{last_close_price:.2f}" if isinstance(last_close_price, float) else last_close_price,
                'Investment': f"{amount_for_symbol:.2f}",
                'Shares': shares
            }
            results.append(result)

    # Add the "Other" group to the results
    results.append({
        'Symbol': 'Other',
        'Name': 'Other',
        'Sector': 'Other',
        'Percentage': f"{other_investment / investment_amount * 100:.2f}%",
        'Last Close Price': 'N/A',
        'Investment': f"{other_investment:.2f}",
        'Shares': 'N/A'
    })

    return pd.DataFrame(results)

def main():
    st.title("Berkshire Portfolio")

    # Custom CSS to increase font size in the DataFrame
    st.markdown("""
        <style>
        .dataframe th, .dataframe td {
            font-size: 25px;  # Adjust the font size as needed
        }
        </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([0.5, 1])

    with col1:
        uploaded_file = st.file_uploader("Upload CSV", type="csv")
        investment_amount = st.number_input("Enter your investment amount ($)", min_value=0.0, value=1000.0)
        if uploaded_file is not None:
            if st.button("Calculate"):
                # Calculate shares and store the result in a DataFrame
                result_df = calculate_shares(pd.read_csv(uploaded_file), investment_amount)

                # Pie Chart for Top 10 Sectors
                result_df['Percentage'] = result_df['Percentage'].str.rstrip('%').astype('float')
                sector_data = result_df.groupby('Sector')['Percentage'].sum().nlargest(10)

                # Create the pie chart with a smaller figure size using subplots
                fig, ax = plt.subplots(figsize=(5, 3))  # Reduce figure size further if needed
                wedges, texts, autotexts = ax.pie(
                    sector_data,
                    labels=sector_data.index,
                    autopct='%1.1f%%',
                    textprops={'fontsize': 5},  # Adjust font size for labels here
                )

                # Set the aspect ratio to be equal so that the pie is drawn as a circle.
                plt.axis('equal')
                plt.title('Top 10 Sectors by Percentage', fontsize=6)  # Adjust title font size here

                # Display the Pie Chart
                st.pyplot(fig)

    with col2:
        if 'result_df' in locals():
            # Display the DataFrame with larger font using Markdown style
            st.markdown(f"{result_df.to_markdown(index=False)}")

if __name__ == "__main__":
    main()
