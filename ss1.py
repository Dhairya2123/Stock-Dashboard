import streamlit as st
import yfinance as yf
import plotly.graph_objs as go
import pandas as pd
import time

st.set_page_config(page_title="Stock Info Dashboard", layout="wide")
st.title("Stock Information App")

# --- User Input ---
ticker = st.text_input("Enter stock ticker (e.g. AAPL, MSFT, TSLA):", "AAPL").upper()

# --- Time Slider ---
st.subheader("Select Time Range")
time_periods = {
    "1 Month": "1mo",
    "3 Months": "3mo",
    "6 Months": "6mo",
    "1 Year": "1y",
    "2 Years": "2y",
    "5 Years": "5y",
    "Max": "max"
}
time_label = st.select_slider("Time Range", options=list(time_periods.keys()), value="6 Months")
time_value = time_periods[time_label]

# --- Data Fetching with 429 Retry Logic ---
def fetch_stock_data(ticker, period="6mo", retries=3, delay=2):
    for attempt in range(retries):
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            hist = stock.history(period=period, interval="1d")

            if hist.empty or "Close" not in hist.columns:
                raise ValueError("No historical data found.")

            return stock, info, hist

        except Exception as e:
            if "429" in str(e) or "Too Many Requests" in str(e):
                st.warning(f"⚠️ Rate limit hit. Retrying in {delay} seconds...")
                time.sleep(delay)
                delay *= 2  # exponential backoff
            else:
                raise e
    raise RuntimeError("Failed after multiple retries due to rate limits or data issues.")

# --- Main Execution ---
if ticker:
    try:
        stock, info, hist = fetch_stock_data(ticker, period=time_value)

        # --- Company Info ---
        st.subheader(" Company Profile")
        company_profile = {
            "Name": info.get("longName", "N/A"),
            "Sector": info.get("sector", "N/A"),
            "Industry": info.get("industry", "N/A"),
            "Market Cap": f"${info.get('marketCap'):,}" if info.get("marketCap") else "N/A",
            "Current Price": info.get("currentPrice", "N/A"),
            "52-Week High": info.get("fiftyTwoWeekHigh", "N/A"),
            "52-Week Low": info.get("fiftyTwoWeekLow", "N/A"),
            "Dividend Yield": f"{info.get('dividendYield') * 100:.2f}%" if info.get("dividendYield") else "N/A"
        }
        st.table(pd.DataFrame.from_dict(company_profile, orient='index', columns=["Value"]))

        # --- Financial Ratios ---
        st.subheader(" Key Financial Ratios")
        ratios = {
            "P/E Ratio": info.get("trailingPE"),
            "P/B Ratio": info.get("priceToBook"),
            "Return on Equity (ROE)": info.get("returnOnEquity"),
            "Return on Assets (ROA)": info.get("returnOnAssets"),
            "Profit Margin": info.get("profitMargins"),
            "Operating Margin": info.get("operatingMargins"),
            "Gross Margin": info.get("grossMargins"),
            "Current Ratio": info.get("currentRatio"),
            "Debt to Equity": info.get("debtToEquity"),
        }
        formatted_ratios = {
            k: f"{v:.2f}" if isinstance(v, (int, float)) and v is not None else "N/A"
            for k, v in ratios.items()
        }
        st.table(pd.DataFrame.from_dict(formatted_ratios, orient='index', columns=["Value"]))

        # --- Price Table ---
        st.subheader(f" Historical Price Data ({time_label})")
        st.dataframe(hist[["Open", "High", "Low", "Close", "Volume"]].sort_index(ascending=False), use_container_width=True)

        # --- Candlestick Chart ---
        st.subheader(" Candlestick Chart")
        fig = go.Figure(data=[go.Candlestick(
            x=hist.index,
            open=hist['Open'],
            high=hist['High'],
            low=hist['Low'],
            close=hist['Close'],
            name=ticker
        )])
        fig.update_layout(
            title=f'{ticker} Candlestick Chart ({time_label})',
            xaxis_title='Date',
            yaxis_title='Price',
            xaxis_rangeslider_visible=True,
            template='plotly_dark'
        )
        st.plotly_chart(fig, use_container_width=True)

    except RuntimeError as e:
        st.error(f" Error: {e}")
    except Exception as e:
        st.error(f" Unexpected Error: {e}")

