import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

#st.set_page_config(layout="wide")  # Enable wide mode
def run_sector_returns():
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
            margin-top: 12px; margin-bottom: 4px
        }
        </style>
    """, unsafe_allow_html=True)

    hint_text = hint("This section allows you to view the performance of a mix of different stocks based on the industry and sector. These are based on research that looks at some of the best performing mutual funds which use similar holdings in their portfolio. Return is a theme’s performance expressed as a percentage change in its price for the past 365 day and the cumulative return is based on the weights assigned ")
    st.markdown(f'<div class="title-container" style="margin-top: -40px; "><h3 style="color: navy; font-size: 30px; margin-top: 4px;">Sector Analysis {hint_text}</h3></div>', unsafe_allow_html=True)

    theme_to_filename = {
        'AI': 'mediacsv.csv',
        'Berkshire': 'Berkshire.csv',
        'Blockchain': 'block.csv',
        'Cloud Service': 'cloud.csv',
        'Custom': 'customstock.csv',
        'Fintech': 'fintech.csv',
        'Gaming': 'games.csv',
        'Health and Fitness': 'fitness.csv',
        'Home and Improvement': 'homeimp.csv',
        'Magnificent 7': 'mag7.csv',
        'Online Services': 'online.csv',
        'Scion Capital': 'Scion Capital.csv'
    }

    selected_theme = st.sidebar.selectbox("Select a Theme:", list(theme_to_filename.keys()))
    filename = theme_to_filename[selected_theme]
    df_theme = pd.read_csv(filename)

    stock_symbols = df_theme["Stock"].tolist()
    stock_weights = df_theme["Weight"].tolist()

    st.subheader("Customize Weights")
    custom_weights_enabled = st.checkbox("Customize weights", value=False)

    update_pressed = False
    custom_weights = stock_weights
    total_weight = 0.0

    col1, col2, col3 = st.columns([0.4,0.2, 0.6])

    with col1:
        investment_amount = st.number_input("Investment Amount ($)", min_value=0.0, value=10000.0, step=500.0)

        if custom_weights_enabled:
            custom_weights = []
            st.markdown("### Adjust Stock Weights")

            weight_inputs = [(stock, st.slider(f"{stock}", min_value=0.0, max_value=1.0, value=stock_weights[idx], step=0.01, key=stock)) for idx, stock in enumerate(stock_symbols)]
            custom_weights = [w for _, w in weight_inputs]  # Moved to top
            total_weight = round(sum(custom_weights), 4)

            st.markdown(f"**Total Weight: {total_weight:.2%}**")
            if total_weight == 1.0:
                update_pressed = st.button("Update Weights")
            elif total_weight > 1.0:
                st.error("Total weight exceeds 100%. Please adjust.")
            elif total_weight < 1.0:
                st.warning("Total weight is less than 100%. Please adjust.")

    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    all_data = pd.DataFrame()
    valid_symbols, valid_weights = [], []

    for ticker, weight in zip(stock_symbols, stock_weights):
        try:
            df_temp = yf.download(ticker, start=start_date, end=end_date, progress=False, auto_adjust=True)
            if df_temp is not None and not df_temp.empty and "Close" in df_temp.columns:
                close_series = df_temp["Close"]
                if isinstance(close_series, pd.DataFrame):
                    close_series = close_series.iloc[:, 0]  # Get first column if multiple

                all_data[ticker] = close_series
                valid_symbols.append(ticker)
                valid_weights.append(weight)
            else:
                st.warning(f"No valid 'Close' price data for {ticker}")
        except Exception as e:
            st.error(f"Failed to download data for {ticker}: {e}")

    if all_data.empty:
        st.error("No valid price data found for the selected theme.")
        return

    daily_returns = all_data.pct_change()

    weighted_returns_default = daily_returns.mul(stock_weights, axis=1)
    overall_daily_return_default = weighted_returns_default.sum(axis=1)
    cumulative_factor_default = (1 + overall_daily_return_default).cumprod()
    cumulative_pct_default = (cumulative_factor_default - 1) * 100.0

    weighted_returns_custom = None
    cumulative_pct_custom = None
    if custom_weights_enabled and update_pressed and abs(total_weight - 1.0) < 0.001:
        weighted_returns_custom = daily_returns.mul(custom_weights, axis=1)
        overall_daily_return_custom = weighted_returns_custom.sum(axis=1)
        cumulative_factor_custom = (1 + overall_daily_return_custom).cumprod()
        cumulative_pct_custom = (cumulative_factor_custom - 1) * 100.0

    final_display_return = cumulative_pct_custom.iloc[-1] if cumulative_pct_custom is not None else cumulative_pct_default.iloc[-1]

    with col3:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=cumulative_pct_default.index,
            y=cumulative_pct_default,
            mode='lines',
            name='Default Weights',
            line=dict(width=2, color='blue', dash='dot')
        ))

        if cumulative_pct_custom is not None:
            fig.add_trace(go.Scatter(
                x=cumulative_pct_custom.index,
                y=cumulative_pct_custom,
                mode='lines',
                name='Custom Weights',
                line=dict(width=2, color='green')
            ))

        fig.update_layout(
            title=f"{selected_theme} – 1YR Cumulative Return: {final_display_return:.2f}%",
            xaxis_title="Date",
            yaxis_title="Cumulative Return (%)",
            template='plotly_dark'
        )
        st.plotly_chart(fig, use_container_width=True)

        latest_prices = all_data.iloc[-1].values
        prices_one_year_ago = all_data.iloc[0].values
        price_changes = latest_prices - prices_one_year_ago
        individual_returns = (latest_prices / prices_one_year_ago - 1) * 100

        weights_used = custom_weights if cumulative_pct_custom is not None else stock_weights
        initial_investments = [investment_amount * w for w in weights_used]
        final_investments = [initial * (1 + r / 100) for initial, r in zip(initial_investments, individual_returns)]
        returns = [final - initial for final, initial in zip(final_investments, initial_investments)]

        summary_df = pd.DataFrame({
            'Stock': stock_symbols,
            'Weight (%)': [f"{w:.2%}" for w in weights_used],
            'Latest Price': [f"${x:.2f}" for x in latest_prices],
            'Price 1 Year Ago': [f"${x:.2f}" for x in prices_one_year_ago],
            'Price Change': [f"${x:.2f}" for x in price_changes],
            'Initial Investment ($)': [f"${x:.2f}" for x in initial_investments],
            'Gain ($)': [f"${x:.2f}" for x in final_investments],
            'Return ($)': [f"${x:.2f}" for x in returns],
            'Return Rate (%)': [f"{x:.2f}%" for x in individual_returns],
        })

        total_row = pd.DataFrame({
            'Stock': ['Total'],
            'Weight (%)': [f"{sum(weights_used):.2%}"],
            'Latest Price': [''],
            'Price 1 Year Ago': [''],
            'Price Change': [''],
            'Initial Investment ($)': [f"${sum(initial_investments):.2f}"],
            'Gain ($)': [f"${sum(final_investments):.2f}"],
            'Return ($)': [f"${sum(returns):.2f}"],
            'Return Rate (%)': ['']
        })

        summary_df = pd.concat([summary_df, total_row], ignore_index=True)

        st.subheader("Detailed Stock Performance")
        st.dataframe(summary_df.style.set_table_styles([
            {'selector': 'thead th', 'props': [('background-color', '#DDEBF7'), ('color', 'black')]},
            {'selector': 'tbody td', 'props': [('text-align', 'left')]}
        ]).highlight_max(axis=0, color='lightgreen').highlight_min(axis=0, color='salmon'), use_container_width=True)


if __name__ == "__main__":
    run_sector_returns()
