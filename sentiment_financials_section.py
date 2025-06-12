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

    hint_text = hint("This section allows you to view the current sentiment for a company based on news snippets and tools like NLTK, VADER Sentiment analysis which assigns a score to the article.")
    st.markdown(f'<div class="title-container" style="margin-top: -2px;"><h2 style="color: navy; font-size: 30px;">Sentiment and Trade Signal {hint_text}</h2></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    sentiment_result = calculate_stock_sentiment(selected_ticker, api_key)

    if "error" in sentiment_result:
        st.error(f"Failed to get sentiment data: {sentiment_result['error']}")
    elif not sentiment_result["article_scores"]:
        st.info("No sentiment data available.")
    else:
        avg = sentiment_result["average_sentiment"]
        st.metric("Average Sentiment", f"{avg:.2f}", delta=f"{avg * 100:.1f}%")

        df_sent = pd.DataFrame(sentiment_result["article_scores"])
        fig = px.bar(
            df_sent,
            x="date",
            y="score",
            color="score",
            color_continuous_scale="RdYlGn",
            title="Sentiment Score per News Article",
            hover_data=["title"]
        )
        fig.update_layout(height=400, margin=dict(t=30, b=30, l=10, r=10))
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("📚 View Analyzed Articles"):
            for article in sentiment_result["article_scores"]:
                st.markdown(f"**{article['date']}** — *{article['title']}*")
                st.progress((article['score'] + 1) / 2)

    # ---------- Financials Section (Embedded below sentiment) ----------

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    url = f"https://financialmodelingprep.com/api/v3/income-statement/{selected_ticker}?period=annual&limit=5&apikey={api_key}"
    data = get_jsonparsed_data(url)

    if data:
        df = pd.DataFrame(data)
        df = df.sort_values('Year')
        df["Y/Y"] = df["Net Income"].pct_change().fillna(0) * 100
        df["Y/Y"] = df["Y/Y"].apply(
            lambda x: f'<span style="color: {"red" if x < 0 else "green"}">{x:.2f}%</span>' if x != '' else ''
        )

        numerical_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        df[numerical_columns] = df[numerical_columns].round(2)

        bar_chart_data = df[["Year", "Revenue", "Net Income"]].copy().set_index("Year")

        st.markdown("### Revenue & Net Income")
        st.bar_chart(bar_chart_data)

        with st.expander("📊 View Table"):
            st.markdown(df[["Year", "Revenue", "Net Income", "Y/Y"]].to_html(escape=False, index=False), unsafe_allow_html=True)

    col1, col2 = st.columns([0.4, 0.35])
    st.session_state.selected_ticker = selected_ticker

    with col1:
        analyze_sentiment(st.session_state.selected_ticker)