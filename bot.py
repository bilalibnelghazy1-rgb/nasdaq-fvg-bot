import yfinance as yf
import time
import requests
import pandas as pd
from datetime import datetime
from threading import Thread
from flask import Flask
import os
import pytz

BOT_TOKEN = os.getenv("BOT_TOKEN", "8715273824:AAFExMirkgU7wfR5VHC6sISrw-5hplfb4Wc")
CHAT_ID = os.getenv("CHAT_ID", "7667675719")

app = Flask(__name__)

@app.route('/')
def home():
    et = get_et_time()
    if is_scan_active():
        status = "SCAN ACTIVE 🟡 Pre-NY" if not is_market_open() else "OPEN 🟢"
    else:
        status = "CLOSED 🔴"
    return f"NASDAQ Bot - {status} - ET: {et.strftime('%H:%M')} - Pre-NY DoL Hunter"

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print(e)

def get_et_time():
    et_tz = pytz.timezone('America/New_York')
    return datetime.now(et_tz)

def is_market_open():
    """9:30 - 16:00 ET - l7el rassi dyal NASDAQ"""
    try:
        et_now = get_et_time()
        if et_now.weekday() >= 5:
            return False
        market_open = et_now.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = et_now.replace(hour=16, minute=0, second=0, microsecond=0)
        return market_open <= et_now <= market_close
    except:
        return True

def is_scan_active():
    """8:00 - 16:00 ET - Pre-NY + NY - fin kaytkhad DoL 9bel NY"""
    try:
        et_now = get_et_time()
        if et_now.weekday() >= 5:
            return False
        scan_start = et_now.replace(hour=8, minute=0, second=0, microsecond=0)
        scan_end = et_now.replace(hour=16, minute=0, second=0, microsecond=0)
        return scan_start <= et_now <= scan_end
    except:
        return True

def get_next_open_message():
    et_now = get_et_time()
    if et_now.weekday() == 5:
        return "Tnin 14:00 Pre-Market / 15:30 OPEN (Maroc)"
    elif et_now.weekday() == 6:
        return "Gheda Tnin 14:00 Pre-Market (Maroc)"
    else:
        return "Gheda 14:00 Pre-Market (Maroc)"

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
    et_now = get_et_time()
    ma_time = et_now.astimezone(pytz.timezone('Africa/Casablanca')).strftime('%H:%M')
    
    # Start message
    if is_market_open():
        send_telegram(f"✅ *NASDAQ Bot V2 - Pre-NY DoL Hunter*
🟢 Market OPEN - ET {et_now.strftime('%H:%M')} | MA {ma_time}
Kay9elleb 30m FVG → 5m DoL → 1m IFVG")
    elif is_scan_active():
        send_telegram(f"✅ *NASDAQ Bot V2 - Pre-NY DoL Hunter*
🟡 Pre-Market SCAN ACTIVE - ET {et_now.strftime('%H:%M')} | MA {ma_time}
Kan9elleb DoL li kaytkhad 9bel NY Open (8:00-9:30 ET)
NY Open: 15:30 MA")
    else:
        send_telegram(f"✅ *NASDAQ Bot V2 - Pre-NY DoL Hunter*
🔴 Market CLOSED
Ghadi ybda scan: {get_next_open_message()}
💡 Kay9elleb DoL 9bel NY - fikra dyalk Bilal!")

    last_market_state = is_market_open()
    last_scan_state = is_scan_active()
    sent_premarket_today = False

    while True:
        try:
            et_now = get_et_time()
            market_open = is_market_open()
            scan_active = is_scan_active()

            # 1. Pre-Market START (8:00 ET = 14:00 MA)
            if scan_active and not last_scan_state:
                ma_time = et_now.astimezone(pytz.timezone('Africa/Casablanca')).strftime('%H:%M')
                send_telegram(f"🟡 *PRE-MARKET SCAN STARTED* ⏳

Bda scan daba! ET 8:00 | MA {ma_time}
Kay9elleb DoL li kaytkhad 9bel NY Open
NY Open f 15:30 MA - Setup kayt-wjed daba 🔍")
                sent_premarket_today = False
                last_scan_state = True

            # 2. NY OPEN (9:30 ET = 15:30 MA)
            if market_open != last_market_state:
                if market_open:
                    ma_time = et_now.astimezone(pytz.timezone('Africa/Casablanca')).strftime('%H:%M')
                    send_telegram(f"🟢 *NASDAQ OPEN* 🔔🔔🔔

Market 7el daba!
ET {et_now.strftime('%H:%M')} | MA {ma_time}
Close 22:00 MA

DoL li tkhad 9bel daba ghadi ykhdem - Bot kay9elleb entry 1m IFVG 🔥")
                else:
                    if et_now.weekday() == 4:
                        send_telegram(f"🔴 *NASDAQ CLOSE - Weekend*
Market sed - Weekend!
Ghadi ybda Pre-Market Tnin 14:00 MA
Bot kay-tsenna... 💤")
                    else:
                        send_telegram(f"🔴 *NASDAQ CLOSE*
Market sed ET {et_now.strftime('%H:%M')}
Ghadi ybda {get_next_open_message()}
Bot kay-tsenna 😴")
                    sent_premarket_today = False
                last_market_state = market_open
                last_scan_state = scan_active

            # Ila ma kaynch scan - n3s 5min
            if not scan_active:
                print(f"[{datetime.now()}] CLOSED - Sleeping ET {et_now.strftime('%H:%M')}")
                time.sleep(300)
                last_scan_state = False
                continue

            # SCAN LOGIC - daba kaykhdem men 8:00 ET!
            print(f"[{datetime.now()}] SCAN ACTIVE - ET {et_now.strftime('%H:%M')} - MarketOpen={market_open}")
            
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

            # LOGIC JDIIDA - Pre-NY
            # 1. Ila 8:00-9:30 ET w kayn FVG + DoL (bla 1m) -> Setup forming
            if not market_open and scan_active and htf_zone and dol:
                if not sent_premarket_today:
                    price = df_1m.iloc[-1]['Close']
                    send_telegram(f"⚠️ *SETUP FORMING - Pre-NY* 🟡\n\nTF: {htf_tf} FVG ✅\nZone: {htf_zone[0]:.1f}-{htf_zone[1]:.1f}\nDoL: {dol} ✅ - Tkhad 9bel NY!\nPrice: {price:.1f}\nET {et_now.strftime('%H:%M')} | MA {et_now.astimezone(pytz.timezone('Africa/Casablanca')).strftime('%H:%M')}\n\n⏳ Kaytsenna 1m IFVG f NY Open 15:30...")
                    sent_premarket_today = True

            # 2. Full setup - men 8:00 ET kaykhdem (machi ghir 9:30)
            if htf_zone and dol and (bull_1m or bear_1m):
                price = df_1m.iloc[-1]['Close']
                side = "LONG 🟢" if bull_1m else "SHORT 🔴"
                session = "PRE-NY 🔥" if not market_open else "NY OPEN"
                msg = f"🔥 *NASDAQ {side} - {session}*\nTF: {htf_tf} FVG\nZone: {htf_zone[0]:.1f}-{htf_zone[1]:.1f}\nDoL: {dol} (Tkhad 9bel NY ✅)\nPrice: {price:.1f}\nET: {et_now.strftime('%H:%M')} | MA: {et_now.astimezone(pytz.timezone('Africa/Casablanca')).strftime('%H:%M')}"
                send_telegram(msg)

            time.sleep(60)
        except Exception as e:
            print(e); time.sleep(60)

Thread(target=bot_loop, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
