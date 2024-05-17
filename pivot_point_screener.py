import ccxt
import pandas as pd
import streamlit as st

def get_available_pairs():
    exchange = ccxt.binance()
    markets = exchange.load_markets()
    pairs = [market for market in markets]
    return pairs

def get_data(symbol, timeframe='1d', limit=365):
    exchange = ccxt.binance()
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    return df

def calculate_pivot_points(df):
    df['Pivot'] = (df['high'] + df['low'] + df['close']) / 3
    df['R1'] = 2 * df['Pivot'] - df['low']
    df['S1'] = 2 * df['Pivot'] - df['high']
    df['R2'] = df['Pivot'] + (df['high'] - df['low'])
    df['S2'] = df['Pivot'] - (df['high'] - df['low'])
    df['R3'] = df['high'] + 2 * (df['Pivot'] - df['low'])
    df['S3'] = df['low'] - 2 * (df['high'] - df['Pivot'])
    return df

def determine_sentiment(df):
    df['ShortTerm'] = df['close'] > df['Pivot']
    df['MidTerm'] = df['close'] > df['Pivot'].rolling(window=7).mean()  # Weekly pivot approximation
    df['LongTerm'] = df['close'] > df['Pivot'].rolling(window=30).mean()  # Monthly pivot approximation
    return df

def color_sentiment(val):
    color = 'lightgreen' if val == 'Bullish' else 'lightcoral'
    return f'background-color: {color}'

# Streamlit interface
st.title("Pivot Point Screener for Cryptocurrencies")

# Fetch available pairs
available_pairs = get_available_pairs()

# Allow multiple symbols selection from a searchable dropdown list
symbols = st.multiselect("Select Crypto Symbols", available_pairs, default=["BTC/USDT", "ETH/USDT"])
timeframe = st.selectbox("Select Timeframe", ['1d', '1h', '1w', '1m'])
limit = st.slider("Number of data points", min_value=30, max_value=1000, value=365)

summary_data = []

for symbol in symbols:
    try:
        data = get_data(symbol, timeframe, limit)
        data = calculate_pivot_points(data)
        data = determine_sentiment(data)

        short_term = "Bullish" if data['ShortTerm'].iloc[-1] else "Bearish"
        mid_term = "Bullish" if data['MidTerm'].iloc[-1] else "Bearish"
        long_term = "Bullish" if data['LongTerm'].iloc[-1] else "Bearish"

        summary_data.append({
            "Symbol": symbol,
            "Short Term": short_term,
            "Mid Term": mid_term,
            "Long Term": long_term,
            "Data": data
        })
    except Exception as e:
        st.error(f"Error fetching data for {symbol}: {str(e)}")

# Display summary table
st.write("Sentiment Summary")
summary_df = pd.DataFrame(summary_data)

# Apply color coding to the sentiment columns
styled_summary_df = summary_df.style.applymap(color_sentiment, subset=['Short Term', 'Mid Term', 'Long Term'])
st.dataframe(styled_summary_df)

# Detailed view
selected_symbol = st.selectbox("Select Symbol for Details", [row["Symbol"] for row in summary_data])
selected_data = next((row["Data"] for row in summary_data if row["Symbol"] == selected_symbol), None)

if selected_data is not None:
    st.write(f"Pivot Points for {selected_symbol} ({timeframe})")
    st.dataframe(selected_data)

    short_term = "Bullish" if selected_data['ShortTerm'].iloc[-1] else "Bearish"
    mid_term = "Bullish" if selected_data['MidTerm'].iloc[-1] else "Bearish"
    long_term = "Bullish" if selected_data['LongTerm'].iloc[-1] else "Bearish"

    st.write("Sentiment Summary for Selected Symbol")
    st.write(f"Short Term: {short_term}")
    st.write(f"Mid Term: {mid_term}")
    st.write(f"Long Term: {long_term}")