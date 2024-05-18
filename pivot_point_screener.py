import ccxt
import pandas as pd
import streamlit as st
import altair as alt

# Function to get available pairs from Binance
def get_available_pairs():
    exchange = ccxt.binance()
    markets = exchange.load_markets()
    pairs = [market for market in markets]
    return pairs

# Function to fetch OHLCV data
def get_data(symbol, timeframe='1d', limit=365):
    exchange = ccxt.binance()
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    return df

# Function to calculate pivot points
def calculate_pivot_points(df):
    df['Pivot'] = (df['high'] + df['low'] + df['close']) / 3
    df['R1'] = 2 * df['Pivot'] - df['low']
    df['S1'] = 2 * df['Pivot'] - df['high']
    df['R2'] = df['Pivot'] + (df['high'] - df['low'])
    df['S2'] = df['Pivot'] - (df['high'] - df['low'])
    df['R3'] = df['high'] + 2 * (df['Pivot'] - df['low'])
    df['S3'] = df['low'] - 2 * (df['high'] - df['Pivot'])
    return df

# Function to determine sentiment
def determine_sentiment(df):
    df['ShortTerm'] = df['close'] > df['Pivot']
    df['MidTerm'] = df['close'] > df['Pivot'].rolling(window=7).mean()  # Weekly pivot approximation
    df['LongTerm'] = df['close'] > df['Pivot'].rolling(window=30).mean()  # Monthly pivot approximation
    return df

# Function to apply color coding for sentiment
def color_sentiment(val):
    color = 'lightgreen' if val == 'Bullish' else 'lightcoral'
    return f'background-color: {color}'

# Streamlit interface
st.title("Pivot Point Screener for Cryptocurrencies")

# Fetch available pairs
available_pairs = get_available_pairs()

# Load saved settings from session state or set defaults
if 'symbols' not in st.session_state:
    st.session_state['symbols'] = ["BTC/USDT", "ETH/USDT"]
if 'timeframe' not in st.session_state:
    st.session_state['timeframe'] = '1d'
if 'limit' not in st.session_state:
    st.session_state['limit'] = 100

# Allow multiple symbols selection from a searchable dropdown list
symbols = st.multiselect("Select Crypto Symbols", available_pairs, default=st.session_state['symbols'])
timeframe = st.selectbox("Select Timeframe", ['1d', '1h', '1w', '1m'], index=['1d', '1h', '1w', '1m'].index(st.session_state['timeframe']))
limit = st.slider("Number of data points", min_value=30, max_value=1000, value=st.session_state['limit'])

# Store the selected settings in session state
if symbols:
    st.session_state['symbols'] = symbols
if timeframe:
    st.session_state['timeframe'] = timeframe
if limit:
    st.session_state['limit'] = limit

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
        })
    except Exception as e:
        st.error(f"Error fetching data for {symbol}: {str(e)}")

# Categorize the projects
def categorize_project(row):
    if row["Short Term"] == "Bearish" and row["Mid Term"] == "Bearish" and row["Long Term"] == "Bearish":
        return "Completely Bearish"
    elif row["Short Term"] == "Bullish" and row["Mid Term"] == "Bullish" and row["Long Term"] == "Bullish":
        return "Completely Bullish"
    else:
        return "Gradually Bullish"

summary_df = pd.DataFrame(summary_data)
summary_df['Category'] = summary_df.apply(categorize_project, axis=1)

# Display summary table
st.write("Sentiment Summary")
styled_summary_df = summary_df.style.applymap(color_sentiment, subset=['Short Term', 'Mid Term', 'Long Term'])
st.dataframe(styled_summary_df)

# Visualization
st.write("Sentiment Visualization")
categories = ['Completely Bearish', 'Gradually Bullish', 'Completely Bullish']
colors = {'Completely Bearish': 'red', 'Gradually Bullish': 'orange', 'Completely Bullish': 'green'}
chart = alt.Chart(summary_df).mark_circle(size=60).encode(
    x='Symbol',
    y=alt.Y('Category', sort=categories, title='Sentiment'),
    color=alt.Color('Category', scale=alt.Scale(domain=list(colors.keys()), range=list(colors.values()))),
    tooltip=['Symbol', 'Short Term', 'Mid Term', 'Long Term']
).interactive()

st.altair_chart(chart, use_container_width=True)

# Detailed view
selected_symbol = st.selectbox("Select Symbol for Details", [row["Symbol"] for row in summary_data])
selected_data = None
for row in summary_data:
    if row["Symbol"] == selected_symbol:
        selected_data = row
        break

if selected_data is not None:
    st.write(f"Sentiment Summary for {selected_symbol}")
    st.write(f"Short Term: {selected_data['Short Term']}")
    st.write(f"Mid Term: {selected_data['Mid Term']}")
    st.write(f"Long Term: {selected_data['Long Term']}")
    # Retrieve the detailed data for the selected symbol
    detailed_data = get_data(selected_symbol, timeframe, limit)
    detailed_data = calculate_pivot_points(detailed_data)
    detailed_data = determine_sentiment(detailed_data)
    st.dataframe(detailed_data)
