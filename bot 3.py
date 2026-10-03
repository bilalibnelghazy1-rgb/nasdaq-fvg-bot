
import yfinance as yf
import time
import requests
import pandas as pd
from datetime import datetime
from threading import Thread
from flask import Flask

BOT_TOKEN = "8715273824:AAFExMirkgU7wfR5VHC6sISrw-5hplfb4Wc"
CHAT_ID = "7667675719"

app = Flask(__name__)

@app.route('/')
def home():
    return "NASDAQ Bot Running FREE 24/5 🔥 - Bilal's Bot"

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print(e)

def get_data(interval="5m", period="1d"):
    try:
        df = yf.download("NQ=F", interval=interval, period=period, progress=False, auto_adjust=True)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df.dropna()
    except:
        return None

def detect_bull_fvg(df):
    if len(df) < 3: return False, None
    if df.iloc[-1]['Low'] > df.iloc[-3]['High']:
        return True, (df.iloc[-3]['High'], df.iloc[-1]['Low'])
    return False, None

def detect_bear_fvg(df):
    if len(df) < 3: return False, None
    if df.iloc[-1]['High'] < df.iloc[-3]['Low']:
        return True, (df.iloc[-1]['High'], df.iloc[-3]['Low'])
    return False, None

def detect_dol(df):
    if len(df) < 21: return None
    ph = df['High'].iloc[-21:-1].max()
    pl = df['Low'].iloc[-21:-1].min()
    last = df.iloc[-1]
    if last['High'] > ph and last['Close'] < ph:
        return f"Bear Sweep {ph:.2f}"
    if last['Low'] < pl and last['Close'] > pl:
        return f"Bull Sweep {pl:.2f}"
    return None

def bot_loop():
    send_telegram("✅ *NASDAQ Bot Started - FREE*\nKhdam f Render FREE 24/5\nKan9elleb 30m FVG → 5m DoL → 1m IFVG")
    while True:
        try:
            print(f"[{datetime.now()}] Checking...")
            df_30m = get_data("30m", "5d")
            df_5m = get_data("5m", "1d")
            df_1m = get_data("1m", "1d")
            if df_5m is None or df_1m is None:
                time.sleep(60); continue
            htf_zone = None; htf_tf = None
            if df_30m is not None:
                b, z = detect_bull_fvg(df_30m)
                be, z2 = detect_bear_fvg(df_30m)
                if b or be:
                    htf_zone = z if b else z2
                    htf_tf = "30m"
            dol = detect_dol(df_5m)
            bull_1m, _ = detect_bull_fvg(df_1m)
            bear_1m, _ = detect_bear_fvg(df_1m)
            if htf_zone and dol and (bull_1m or bear_1m):
                price = df_1m.iloc[-1]['Close']
                side = "LONG 🟢" if bull_1m else "SHORT 🔴"
                msg = f"🔥 *NASDAQ {side}*\nTF: {htf_tf} FVG\nZone: {htf_zone[0]:.1f}-{htf_zone[1]:.1f}\nDoL: {dol}\nPrice: {price:.1f}\nTime: {datetime.now().strftime('%H:%M')}"
                send_telegram(msg)
            time.sleep(60)
        except Exception as e:
            print(e); time.sleep(60)

Thread(target=bot_loop, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
