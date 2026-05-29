from flask import Flask, jsonify
import requests
import pandas as pd

app = Flask(__name__)

API_KEY = "demo"
SYMBOL = "EUR/USD"

def get_data():
    url = f"https://api.twelvedata.com/time_series?symbol={SYMBOL}&interval=1min&apikey={API_KEY}&outputsize=100"

    response = requests.get(url)
    data = response.json()

    candles = data["values"]

    df = pd.DataFrame(candles)
    df = df.iloc[::-1]

    df["open"] = df["open"].astype(float)
    df["close"] = df["close"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)

    return df

def analyze_market():

    df = get_data()

    close = df["close"]

    ema9 = close.ewm(span=9).mean()
    ema21 = close.ewm(span=21).mean()

    delta = close.diff()

    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    latest_rsi = rsi.iloc[-1]

    last = df.iloc[-1]

    body = abs(last["close"] - last["open"])

    bullish = last["close"] > last["open"]
    bearish = last["close"] < last["open"]

    resistance = df["high"].tail(20).max()
    support = df["low"].tail(20).min()

    price = last["close"]

    call_score = 0
    put_score = 0

    # EMA
    if ema9.iloc[-1] > ema21.iloc[-1]:
        call_score += 2
    else:
        put_score += 2

    # RSI
    if latest_rsi > 55:
        call_score += 2

    if latest_rsi < 45:
        put_score += 2

    # Candle psychology
    if bullish and body > 0.0001:
        call_score += 2

    if bearish and body > 0.0001:
        put_score += 2

    # Breakout
    if price >= resistance:
        call_score += 3

    if price <= support:
        put_score += 3

    signal = "WAIT"

    if call_score > put_score:
        signal = "CALL"

    if put_score > call_score:
        signal = "PUT"

    return {
        "signal": signal,
        "price": price,
        "rsi": round(latest_rsi,2),
        "call_score": call_score,
        "put_score": put_score
    }

@app.route("/signal")
def signal():
    return jsonify(analyze_market())

@app.route("/")
def home():
    return "ABHI REAL SIGNAL ENGINE RUNNING"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
