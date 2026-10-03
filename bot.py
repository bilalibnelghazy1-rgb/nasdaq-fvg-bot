
import yfinance as yf
import time
import requests
import pandas as pd
from datetime import datetime

# === CONFIG DYALK ===
BOT_TOKEN = "8715273824:AAFExMirkgU7wfR5VHC6sISrw-5hplfb4Wc"
CHAT_ID = "7667675719"

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
        requests.post(url, data=data, timeout=10)
        print(f"[{datetime.now()}] Sent: {msg[:50]}...")
    except Exception as e:
        print(f"Telegram Error: {e}")

def get_data(symbol="NQ=F", interval="5m", period="1d"):
    try:
        df = yf.download(symbol, interval=interval, period=period, progress=False, auto_adjust=True)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df.dropna()
    except Exception as e:
        print(f"Data Error {interval}: {e}")
        return None

def detect_bull_fvg(df):
    # Bull FVG: low > high[2]
    if len(df) < 3:
        return False, None
    last = df.iloc[-1]
    prev2_high = df.iloc[-3]['High']
    if last['Low'] > prev2_high:
        return True, (prev2_high, last['Low'])
    return False, None

def detect_bear_fvg(df):
    if len(df) < 3:
        return False, None
    last = df.iloc[-1]
    prev2_low = df.iloc[-3]['Low']
    if last['High'] < prev2_low:
        return True, (last['High'], prev2_low)
    return False, None

def detect_dol_sweep(df):
    if len(df) < 21:
        return None
    prev_high = df['High'].iloc[-21:-1].max()
    prev_low = df['Low'].iloc[-21:-1].min()
    last = df.iloc[-1]
    if last['High'] > prev_high and last['Close'] < prev_high:
        return f"Bearish DoL Sweep High @ {prev_high:.2f}"
    if last['Low'] < prev_low and last['Close'] > prev_low:
        return f"Bullish DoL Sweep Low @ {prev_low:.2f}"
    return None

def check_setup():
    print(f"\n[{datetime.now()}] Checking NASDAQ...")
    
    # Get higher TF
    df_30m = get_data(interval="30m", period="5d")
    df_15m = get_data(interval="15m", period="5d")
    df_5m = get_data(interval="5m", period="1d")
    df_1m = get_data(interval="1m", period="1d")
    
    if df_5m is None or df_1m is None:
        return
    
    # Step 1: HTF FVG
    htf_zone = None
    htf_tf = None
    
    if df_30m is not None and len(df_30m) > 3:
        bull, zone = detect_bull_fvg(df_30m)
        bear, zone2 = detect_bear_fvg(df_30m)
        if bull or bear:
            htf_zone = zone if bull else zone2
            htf_tf = "30m"
            direction = "BULLISH" if bull else "BEARISH"
            print(f"  -> {htf_tf} FVG Found {direction}: {htf_zone}")
    
    if not htf_zone and df_15m is not None:
        bull, zone = detect_bull_fvg(df_15m)
        bear, zone2 = detect_bear_fvg(df_15m)
        if bull or bear:
            htf_zone = zone if bull else zone2
            htf_tf = "15m"
            direction = "BULLISH" if bull else "BEARISH"
            print(f"  -> {htf_tf} FVG Found {direction}: {htf_zone}")
    
    # Step 2: 5m DoL
    dol = detect_dol_sweep(df_5m)
    if dol:
        print(f"  -> 5m {dol} ✅")
    
    # Step 3: 1m IFVG Entry
    bull_1m, _ = detect_bull_fvg(df_1m)
    bear_1m, _ = detect_bear_fvg(df_1m)
    
    # Logic dyalk: ila kayn HTF FVG + 5m DoL + 1m IFVG => SIGNAL
    if htf_zone and dol and (bull_1m or bear_1m):
        price = df_1m.iloc[-1]['Close']
        rr_text = "12R+" if htf_tf == "30m" else "6R+"
        side = "LONG 🟢" if bull_1m else "SHORT 🔴"
        
        msg = f"""🔥 *NASDAQ SIGNAL - {side}*
        
*Setup:* {htf_tf} FVG → 5m DoL ✅ → 1m IFVG
*Zone:* {htf_zone[0]:.2f} - {htf_zone[1]:.2f}
*DoL:* {dol}
*Price:* {price:.2f}
*Expected RR:* {rr_text}
*Time:* {datetime.now().strftime('%H:%M:%S')}

Action: Check 1m chart NOW - SL sghir = close candle, SL kbir = retest 1m IFVG
MNQ1!"""
        send_telegram(msg)
    else:
        # Send heartbeat every 30 min to know bot is alive (optional)
        pass

# === START ===
send_telegram("✅ *NASDAQ FVG Bot Started*\nBot dyalk khdam daba f Render FREE!\nKan9elleb 30m FVG → 5m DoL → 1m IFVG kol 1 min 🔍")

while True:
    try:
        check_setup()
        time.sleep(60)  # Check kol 1 minute
    except Exception as e:
        print(f"Loop Error: {e}")
        time.sleep(60)
