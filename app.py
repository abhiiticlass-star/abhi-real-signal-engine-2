from flask import Flask, jsonify
from flask_cors import CORS
import requests
import pandas as pd
import ta

app = Flask(__name__)
CORS(app)

SYMBOL = "EURUSD=X"

def get_market_data():

    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{SYMBOL}?interval=1m&range=1d"

    data = requests.get(url).json()

    result = data["chart"]["result"][0]

    closes = result["indicators"]["quote"][0]["close"]
    highs = result["indicators"]["quote"][0]["high"]
    lows = result["indicators"]["quote"][0]["low"]

    df = pd.DataFrame({
        "close": closes,
        "high": highs,
        "low": lows
    })

    df.dropna(inplace=True)

    return df

@app.route("/signal")
def signal():

    df = get_market_data()

    close = df["close"]

    current_price = round(close.iloc[-1], 5)

    # RSI
    rsi = ta.momentum.RSIIndicator(close).rsi().iloc[-1]

    # EMA
    ema_fast = ta.trend.EMAIndicator(close, window=9).ema_indicator().iloc[-1]
    ema_slow = ta.trend.EMAIndicator(close, window=21).ema_indicator().iloc[-1]

    # SUPPORT / RESISTANCE
    support = round(df["low"].tail(20).min(),5)
    resistance = round(df["high"].tail(20).max(),5)

    # BREAKOUT
    breakout_up = current_price > resistance
    breakout_down = current_price < support

    # CANDLE PSYCHOLOGY
    last_candle = close.iloc[-1]
    prev_candle = close.iloc[-2]

    bullish_candle = last_candle > prev_candle
    bearish_candle = last_candle < prev_candle

    # ENGULFING
    bullish_engulf = (
        close.iloc[-1] > close.iloc[-2]
        and close.iloc[-2] < close.iloc[-3]
    )

    bearish_engulf = (
        close.iloc[-1] < close.iloc[-2]
        and close.iloc[-2] > close.iloc[-3]
    )

    call_score = 0
    put_score = 0

    # RSI LOGIC
    if rsi < 35:
        call_score += 20

    if rsi > 65:
        put_score += 20

    # EMA TREND
    if ema_fast > ema_slow:
        call_score += 25
    else:
        put_score += 25

    # CANDLE PSYCHOLOGY
    if bullish_candle:
        call_score += 15

    if bearish_candle:
        put_score += 15

    # ENGULFING
    if bullish_engulf:
        call_score += 20

    if bearish_engulf:
        put_score += 20

    # BREAKOUT
    if breakout_up:
        call_score += 20

    if breakout_down:
        put_score += 20

    signal = "WAIT"

    if call_score >= 60:
        signal = "CALL"

    if put_score >= 60:
        signal = "PUT"

    accuracy = max(call_score, put_score)

    return jsonify({
        "signal": signal,
        "price": current_price,
        "rsi": round(rsi,2),
        "ema_fast": round(ema_fast,5),
        "ema_slow": round(ema_slow,5),
        "support": support,
        "resistance": resistance,
        "call_score": call_score,
        "put_score": put_score,
        "accuracy": accuracy,
        "bullish_engulfing": bullish_engulf,
        "bearish_engulfing": bearish_engulf,
        "breakout_up": breakout_up,
        "breakout_down": breakout_down
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
