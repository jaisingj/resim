def financial_dashboard_function(selected_name):
    import streamlit as st
    import pandas as pd
    from io import BytesIO
    from millify import millify
    import plotly.graph_objs as go
    import sys
    from utils import (
        config_menu_footer, generate_card, empty_lines, get_delta, color_highlighter
    )
    from data import (
        get_income_statement, get_balance_sheet, get_stock_price, get_company_info,
        get_financial_ratios, get_key_metrics, get_cash_flow
    )
    
    df_tickers = pd.read_csv('tickers.csv')
    
    from utils import (
        config_menu_footer, generate_card, empty_lines, get_delta, color_highlighter
    )
    from data import (
        get_income_statement, get_balance_sheet, get_stock_price, get_company_info,
        get_financial_ratios, get_key_metrics, get_cash_flow
    )
    
    # Define caching functions for each API call
    @st.cache_data(ttl=60*60*24*30) # cache output for 30 days
    def company_info(symbol):
        return get_company_info(symbol)
    
    @st.cache_data(ttl=60*60*24*30) # cache output for 30 days
    def income_statement(symbol):
        return get_income_statement(symbol)
    
    @st.cache_data(ttl=60*60*24*30) # cache output for 30 days
    def balance_sheet(symbol):
        return get_balance_sheet(symbol)
    
    @st.cache_data(ttl=60*60*24*30) # cache output for 30 days
    def stock_price(symbol):
        return get_stock_price(symbol)
    
    @st.cache_data(ttl=60*60*24*30) # cache output for 30 days
    def financial_ratios(symbol):
        return get_financial_ratios(symbol)
    
    @st.cache_data(ttl=60*60*24*30) # cache output for 30 days
    def key_metrics(symbol):
        return get_key_metrics(symbol)
    
    @st.cache_data(ttl=60*60*24*30) # cache output for 30 days
    def cash_flow(symbol):
        return get_cash_flow(symbol)
    
    # Define caching function for delta
    @st.cache_data(ttl=60*60*24*30) # cache output for 30 days
    def delta(df, key):
        return get_delta(df, key)
    
    # Configure the menu and footer with the user's information
    config_menu_footer()
    
    # Display the app title
    # st.title("Financial Dashboard 📈")
    
    # Check if a company name is selected
    if selected_name:
        selected_ticker = df_tickers[df_tickers['Name'] == selected_name]['Symbol'].values[0]
        st.session_state.selected_ticker = selected_ticker
    
        # Check if the user has entered a valid ticker symbol
        try:
            symbol_input = st.session_state.selected_ticker
            # Call the API functions to get the necessary data for the dashboard
            company_data = get_company_info(symbol_input)
            metrics_data = key_metrics(symbol_input)
            income_data = income_statement(symbol_input)
            performance_data = stock_price(symbol_input)
            ratios_data = financial_ratios(symbol_input)
            balance_sheet_data = balance_sheet(symbol_input)
            cashflow_data = cash_flow(symbol_input)
    
        except Exception as e:
            st.error('Not possible to retrieve data for that ticker. Please check if it\'s valid and try again.')
            sys.exit()
    
        # Display dashboard
        empty_lines(2)
        try:
            # Display company info
            col1, col2 = st.columns((8.5,1.5))
            with col1:
                generate_card(company_data['Name'])
            with col2:
                # display image and make it clickable
                image_html = f"<a href='{company_data['Website']}' target='_blank'><img src='{company_data['Image']}' alt='{company_data['Name']}' height='75' width='95'></a>"
                st.markdown(image_html, unsafe_allow_html=True)
    
            col3, col4, col5, col6, col7 = st.columns((0.2,1.3,1.3,2,2.6))
    
            with col4:
                empty_lines(1)
                st.markdown("<p style='font-size: 25px; margin-top: 10px; margin-bottom: -40px;'>Price</p>", unsafe_allow_html=True)

                st.metric(label="", value=company_data['Price'], delta=company_data['Price change'])
                empty_lines(2)
    
            with col5:
                empty_lines(1)
                generate_card(company_data['Currency'])
                empty_lines(2)
    
            with col6:
                empty_lines(1)
                generate_card(company_data['Exchange'])
                empty_lines(2)
    
            with col7:
                empty_lines(1)
                generate_card(company_data['Sector'])            
                empty_lines(2)
    
            # Define columns for key metrics and IS
            col8, col9, col10, col11, col12, col13 = st.columns((3,3,2,4,2,1))
    
            # Display key metrics  
            with col8:
                empty_lines(3)
                st.markdown("<p style='font-size: 25px; margin-top: 10px; margin-bottom: -40px;'>Market Cap</p>", unsafe_allow_html=True)

                st.metric(label="", value=millify(metrics_data['Market Cap'][0], precision=2), delta=delta(metrics_data,'Market Cap'))
                st.write("")
                st.markdown("<p style='font-size: 25px; margin-top: 10px; margin-bottom: -40px;'>D/E Ratio</p>", unsafe_allow_html=True)

                st.metric(label="", value = round(metrics_data['D/E ratio'][0],2), delta=delta(metrics_data,'D/E ratio'))
                st.write("")
                st.markdown("<p style='font-size: 25px; margin-top: 10px; margin-bottom: -40px;'>ROE</p>", unsafe_allow_html=True)
                st.metric(label="", value = str(round(metrics_data['ROE'][0] * 100, 2)) + '%', delta=delta(metrics_data,'ROE'))
    
            with col9:
                empty_lines(3)
                    
                st.markdown("<p style='font-size: 25px; margin-top: 10px; margin-bottom: -40px;'>Working Capital</p>", unsafe_allow_html=True)
                st.metric(label="", value = millify(metrics_data['Working Capital'][0], precision = 2), delta=delta(metrics_data,'Working Capital'))
                st.write("")
                #st.markdown("<h3 style='font-size: 10px; '>P/E Ratio</h3>", unsafe_allow_html=True)
                st.markdown("<p style='font-size: 25px; margin-top: 10px; margin-bottom: -40px;'>P/E Ratio</p>", unsafe_allow_html=True)
                st.metric(label="", value = round(metrics_data['P/E Ratio'][0],2), delta=delta(metrics_data,'P/E Ratio'))
                st.write("")
                # Check if the company pays dividends
                if metrics_data['Dividend Yield'][0] == 0:
                    st.markdown("<p style='font-size: 25px; margin-top: 10px; margin-bottom: -40px;'>Dividends (yield)</p>", unsafe_allow_html=True)
                    st.metric(label="", value = '0')
                else:
                    st.markdown("<p style='font-size: 25px; margin-top: 10px; margin-bottom: -40px;'>Dividends (yield)</p>", unsafe_allow_html=True)
                    st.metric(label="", value = str(round(metrics_data['Dividend Yield'][0]* 100, 2)) + '%', delta=delta(metrics_data,'Dividend Yield'))
            with col11:      
                # Transpose the income data so that the years are the columns
                income_statement_data = income_data.T
    
                # Display a markdown header for the income statement
                st.markdown('**Income Statement**')
                            
                # Allow the user to select a year to display
                year = st.selectbox('All numbers in thousands', income_statement_data.columns, label_visibility='collapsed')
    
                # Slice the income data to only show the selected year and format numbers with millify function
                income_statement_data = income_statement_data.loc[:, [year]]
                # Apply millify to each value (using apply for pandas 2.0+ compatibility)
                income_statement_data = income_statement_data.apply(lambda x: x.apply(lambda y: millify(y, precision=2)))
                            
                # Apply the color_highlighter function to highlight negative numbers
                income_statement_data = income_statement_data.style.map(color_highlighter)
    
                # Style the table headers with black color
                headers = {
                    'selector': 'th:not(.index_name)',
                    'props': [('color', 'black')]
                }
    
                income_statement_data.set_table_styles([headers])
    
                # Display the income statement table in Streamlit
                st.table(income_statement_data)

                
        except Exception as e:
            st.error('An error occurred while displaying the dashboard. Please try again.')
        
        # Create a new set of columns for the chart outside of col10
        col11, col12, col13 = st.columns([0.3, 0.2, 0.5])
        with col11:
            st.write("")
            st.write("## Market Performance")
            st.write("")
        
            # Configure the plots bar
            config = {
                'displaylogo': False, 
                'modeBarButtonsToRemove': ['zoom2d', 'pan2d', 'select2d', 'lasso2d', 'hoverClosestCartesian', 'hoverCompareCartesian', 'autoScale2d', 'toggleSpikelines', 'resetScale2d', 'zoomIn2d', 'zoomOut2d', 'hoverClosest3d', 'hoverClosestGeo', 'hoverClosestGl2d', 'hoverClosestPie', 'toggleHover', 'resetViews', 'toggleSpikeLines', 'resetViewMapbox', 'resetGeo', 'hoverClosestGeo', 'sendDataToCloud', 'hoverClosestGl']
            }

            # Determine the color of the line based on the first and last prices
            line_color = 'rgb(60, 179, 113)' if performance_data.iloc[0]['Price'] > performance_data.iloc[-1]['Price'] else 'rgb(255, 87, 48)'

            # Create the line chart for Market Performance
            fig1 = go.Figure(
                go.Scatter(
                    x=performance_data.index,
                    y=performance_data['Price'],
                    mode='lines',
                    name='Price',
                    line=dict(color='blue')
                )
            )


            fig1.update_layout(
                #title_text='Market Performance',
                dragmode='pan',
                xaxis=dict(
                    fixedrange=True
                ),
                yaxis=dict(
                    fixedrange=True
                ),
                legend=dict(orientation='h', x=0.1, y=1.2, traceorder='normal'),
                height=400
            )

            # Render the line chart for Market Performance in col14
            st.plotly_chart(fig1, config=config, use_container_width=True)
            
            # Display balance sheet
            # Create a vertical bar chart of Assets and Liabilities
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=balance_sheet_data.index,
                y=balance_sheet_data['Assets'],
                name='Assets',
                marker=dict(color='green'),
                width=0.3,
            ))
            fig.add_trace(go.Bar(
                x=balance_sheet_data.index,
                y=balance_sheet_data['Liabilities'],
                name='Liabilities',
                marker=dict(color='navy'),
                width=0.3,
            ))

            # Add a line for assets
            fig.add_trace(go.Scatter(
                x=balance_sheet_data.index,
                y=balance_sheet_data['Equity'],
                mode='lines+markers',
                name='Equity',
                line=dict(color='red',dash='dot', width=3),
                
            ))

            # Update layout
            st.write("## Balance Sheet")
            fig.update_layout(
                #title='Balance Sheet',
                bargap=0.4,
                dragmode='pan',
                xaxis=dict(
                    fixedrange=True
                ),
                yaxis=dict(
                    fixedrange=True,
                ),
                legend=dict(orientation='h', x=0.1, y=1.2, traceorder='normal'),
                height=400
            )

            # Display the plot 
            st.plotly_chart(fig, config=config, use_container_width=True)

            # Display ROE and ROA
            # Create the line chart 
            st.write("## ROE vs ROA")
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=ratios_data.index,
                y=ratios_data['Return on Equity'],
                name='ROE',
                line=dict(color='rgba(60, 179, 113, 0.85)'),
            ))
            fig.add_trace(go.Scatter(
                x=ratios_data.index,
                y=ratios_data['Return on Assets'],
                name='ROA',
                line=dict(color='rgba(30, 144, 255, 0.85)'),
            ))
    
            # Update layout
            fig.update_layout(
                #title='ROE and ROA',
                dragmode='pan',
                xaxis=dict(
                    fixedrange=True
                ),
                yaxis=dict(
                    fixedrange=True,
                    tickformat='.0%'
                ),
                legend=dict(orientation='h', x=0.1, y=1.2, traceorder='normal'),  # Set legend orientation to horizontal and position it at the top

                height=500
            )
    
            # Display the plot in Streamlit
            st.plotly_chart(fig, config=config, use_container_width=True)

            

        # Create a new set of columns for the "Net Income" chart in col15
        with col13:
            st.write("")
            st.write("## Net Income")
            st.write("")

            # Create the line chart for Net Income
            fig2 = go.Figure()
            fig2.add_trace(
                go.Scatter(
                    x=income_data.index, 
                    y=income_data["= Net Income"], 
                    mode="lines+markers", 
                    line=dict(color="green", smoothing=1.3), 
                    marker=dict(size=5)
                )
            )

            # Customize the chart layout for Net Income
            fig2.update_layout(
                #title="Net Income",
                dragmode='pan',
                xaxis=dict(
                    tickmode='array', 
                    tickvals=income_data.index,
                    fixedrange=True
                ),
                yaxis=dict(
                    fixedrange=True
                ),
                height=400,
                legend=dict(orientation='h', x=0.1, y=1.2, traceorder='normal'),  # Set legend orientation to horizontal and position it at the top
                margin=dict(l=20, r=20, t=40, b=20),
       
            )

            # Render the chart for Net Income in col15
            st.plotly_chart(fig2, config=config, use_container_width=True)


            
    
            # Create an horizontal bar chart of profitability margins
            st.write("## Profit Margins")
            fig3 = go.Figure()
            fig3.add_trace(go.Bar(
                y=ratios_data.index,
                x=ratios_data['Gross Profit Margin'],
                name='Gross Profit Margin',
                marker=dict(color='rgba(60, 179, 113, 0.85)'),
                orientation='h',
            ))
            fig3.add_trace(go.Bar(
                y=ratios_data.index,
                x=ratios_data['Operating Profit Margin'],
                name='EBIT Margin',
                marker=dict(color='rgba(30, 144, 255, 0.85)'),
                orientation='h',
            ))

            fig3.add_trace(go.Bar(
                y=ratios_data.index,
                x=ratios_data['Net Profit Margin'],
                name='Net Profit Margin',
                marker=dict(color='rgba(173, 216, 230, 0.85)'),
                orientation='h',
            ))

            # Update layout
            fig3.update_layout(
                #title='Profitability Margins',
                bargap=0.1,
                dragmode='pan',
                xaxis=dict(
                    fixedrange=True,
                    tickformat='.0%'
                ),
                yaxis=dict(
                    fixedrange=True
                ),
                height=400,
                legend=dict(orientation='h', x=0.1, y=1.2, traceorder='normal'),  # Set legend orientation to horizontal and position it at the top
                margin=dict(l=20, r=20, t=40, b=20),
            )

            # Display the plot for Profitability Margins
            st.plotly_chart(fig3, config=config, use_container_width=True)

            # Display cash flows
            # Create a vertical bar chart of Cash flows
            st.write("## Cash Flows")
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=cashflow_data.index,
                y=cashflow_data['Cash flows from operating activities'],
                name='Cash flows from operating activities',
                marker=dict(color='rgba(60, 179, 113, 0.85)'),
                width=0.3,
            ))
            fig.add_trace(go.Bar(
                x=cashflow_data.index,
                y=cashflow_data['Cash flows from investing activities'],
                name='Cash flows from investing activities',
                marker=dict(color='rgba(30, 144, 255, 0.85)'),
                width=0.3,
            ))
    
            fig.add_trace(go.Bar(
                x=cashflow_data.index,
                y=cashflow_data['Cash flows from financing activities'],
                name='Cash flows from financing activities',
                marker=dict(color='rgba(173, 216, 230, 0.85)'),
                width=0.3,
            ))
    
            # Add a line for Free cash flow
            fig.add_trace(go.Scatter(
                x=cashflow_data.index,
                y=cashflow_data['Free cash flow'],
                mode='lines+markers',
                name='Free cash flow',
                line=dict(color='rgba(255, 140, 0, 1)', width=2),
                marker=dict(symbol='circle', size=5, color='rgba(255, 140, 0, 1)', line=dict(width=0.8, color='rgba(255, 140, 0, 1)'))
            ))
    
            # Update layout
            fig.update_layout(
                #title='Cash flows',
                bargap=0.1,
                    xaxis=dict(
                    fixedrange=True,
                ),
                yaxis=dict(
                    fixedrange=True,

                ),

                height=500,
                legend=dict(orientation='h', x=0.1, y=1.2, traceorder='normal')  # Set legend orientation to horizontal and position it at the top


            )
    
            # Display the plot 
            st.plotly_chart(fig, config=config, use_container_width=True)
