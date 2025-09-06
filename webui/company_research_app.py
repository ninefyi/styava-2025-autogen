import streamlit as st
from dotenv import load_dotenv
import os
import requests
from bs4 import BeautifulSoup
import yfinance as yf
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pytz import timezone

load_dotenv()

def google_search(query: str, num_results: int = 2, max_chars: int = 500):
    api_key = os.getenv("GOOGLE_API_KEY")
    search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
    url = "https://customsearch.googleapis.com/customsearch/v1"
    params = {"key": api_key, "cx": search_engine_id, "q": query, "num": num_results}
    response = requests.get(url, params=params)
    results = response.json().get("items", [])
    def get_page_content(url: str) -> str:
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, "html.parser")
            text = soup.get_text(separator=" ", strip=True)
            words = text.split()
            content = ""
            for word in words:
                if len(content) + len(word) + 1 > max_chars:
                    break
                content += " " + word
            return content.strip()
        except Exception as e:
            return ""
    enriched_results = []
    for item in results:
        body = get_page_content(item["link"])
        enriched_results.append(
            {"title": item["title"], "link": item["link"], "snippet": item["snippet"], "body": body}
        )
    return enriched_results

def analyze_stock(ticker: str):
    end_date = pd.Timestamp.now(tz="UTC")
    start_date = end_date - pd.Timedelta(days=365)
    stock = yf.Ticker(ticker)
    hist = stock.history(start=start_date, end=end_date)
    if hist.empty:
        return {"error": "No historical data available for the specified ticker."}
    current_price = stock.info.get("currentPrice", hist["Close"].iloc[-1])
    year_high = stock.info.get("fiftyTwoWeekHigh", hist["High"].max())
    year_low = stock.info.get("fiftyTwoWeekLow", hist["Low"].min())
    ma_50 = hist["Close"].rolling(window=50).mean().iloc[-1]
    ma_200 = hist["Close"].rolling(window=200).mean().iloc[-1]
    ytd_start = pd.Timestamp(end_date.year, 1, 1, tz="UTC")
    ytd_data = hist.loc[ytd_start:]
    if not ytd_data.empty:
        price_change = ytd_data["Close"].iloc[-1] - ytd_data["Close"].iloc[0]
        percent_change = (price_change / ytd_data["Close"].iloc[0]) * 100
    else:
        price_change = percent_change = np.nan
    if pd.notna(ma_50) and pd.notna(ma_200):
        if ma_50 > ma_200:
            trend = "Upward"
        elif ma_50 < ma_200:
            trend = "Downward"
        else:
            trend = "Neutral"
    else:
        trend = "Insufficient data for trend analysis"
    daily_returns = hist["Close"].pct_change().dropna()
    volatility = daily_returns.std() * np.sqrt(252)
    result = {
        "ticker": ticker,
        "current_price": current_price,
        "52_week_high": year_high,
        "52_week_low": year_low,
        "50_day_ma": ma_50,
        "200_day_ma": ma_200,
        "ytd_price_change": price_change,
        "ytd_percent_change": percent_change,
        "trend": trend,
        "volatility": volatility,
    }
    plt.figure(figsize=(12, 6))
    plt.plot(hist.index, hist["Close"], label="Close Price")
    plt.plot(hist.index, hist["Close"].rolling(window=50).mean(), label="50-day MA")
    plt.plot(hist.index, hist["Close"].rolling(window=200).mean(), label="200-day MA")
    plt.title(f"{ticker} Stock Price (Past Year)")
    plt.xlabel("Date")
    plt.ylabel("Price ($)")
    plt.legend()
    plt.grid(True)
    st.pyplot(plt)
    return result

st.title("Company Research App")

company = st.text_input("Enter company name (for search):", "American Airlines")
ticker = st.text_input("Enter stock ticker:", "AAL")

if st.button("Search Company Info"):
    with st.spinner("Searching..."):
        results = google_search(company)
        for r in results:
            st.subheader(r["title"])
            st.write(r["snippet"])
            st.write(r["body"])
            st.write(f"[Link]({r['link']})")

if st.button("Analyze Stock"):
    with st.spinner("Analyzing..."):
        stock_info = analyze_stock(ticker)
        if "error" in stock_info:
            st.error(stock_info["error"])
        else:
            st.json(stock_info)

if st.button("Generate Report"):
    st.write("## Report")
    st.write(f"Company: {company}")
    st.write(f"Ticker: {ticker}")
    # You can add more logic to combine search and stock info here
