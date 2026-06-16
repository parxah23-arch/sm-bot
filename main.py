import ccxt
import pandas as pd
import requests

TELEGRAM_TOKEN = "8938113316:AAH5MYho79ykj244FLvSXfWBZo4MfZh-Jc"
TELEGRAM_CHAT_ID = "8578491445"
MONETS = ['XAUUSD', 'GER40']  
exchange = ccxt.bingx({'enableRateLimit': True})

def send_telegram_message(message):
    url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try: requests.post(url, json=payload, timeout=10)
    except: pass

def get_candles(symbol, timeframe):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=100)
        return pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    except: return None

def check_fvg_15m(df):
    if df is None or len(df) < 5: return None
    last_close = df['close'].iloc[-1]
    low_1, high_3 = df['low'].iloc[-2], df['high'].iloc[-4]
    if low_1 > high_3 and high_3 <= last_close <= low_1: return "BULLISH_FVG"
    high_1, low_3 = df['high'].iloc[-2], df['low'].iloc[-4]
    if high_1 < low_3 and high_1 <= last_close <= low_3: return "BEARISH_FVG"
    return None

def detect_choch_5m(df):
    if df is None or len(df) < 10: return None
    df['hh'] = df['high'] == df['high'].rolling(5, center=True).max()
    df['ll'] = df['low'] == df['low'].rolling(5, center=True).min()
    last_close, prev_close = df['close'].iloc[-1], df['close'].iloc[-2]
    recent_highs = df[df['hh'] == True]['high'].tail(2).values
    recent_lows = df[df['ll'] == True]['low'].tail(2).values
    if len(recent_highs) < 1 or len(recent_lows) < 1: return None
    if prev_close <= recent_highs[-1] and last_close > recent_highs[-1]: return "BULLISH_CHOCH"
    if prev_close >= recent_lows[-1] and last_close < recent_lows[-1]: return "BEARISH_CHOCH"
    return None

def check_trend_1h(df):
    if df is None or len(df) < 50: return "NEUTRAL"
    ema = df['close'].ewm(span=50, adjust=False).mean()
    return "LONG" if df['close'].iloc[-1] > ema.iloc[-1] else "SHORT"

def check_market_once():
    # Проверяем рынок один раз (без бесконечного цикла)
    for monet in MONETS:
        df_1h = get_candles(monet, '1h')
        df_15m = get_candles(monet, '15m')
        df_5m = get_candles(monet, '5m')
        
        if df_1h is None or df_15m is None or df_5m is None: continue
            
        trend_1h = check_trend_1h(df_1h)
        fvg_15m = check_fvg_15m(df_15m)
        choch_5m = detect_choch_5m(df_5m)
        
        if trend_1h == "LONG" and fvg_15m == "BULLISH_FVG" and choch_5m == "BULLISH_CHOCH":
            send_telegram_message(f"🟢 *SMART MONEY: LONG*\n📊 #{monet}\n📈 1H: LONG\n⏳ 15M: Тест FVG\n⚡️ 5M: Слом CHOCH!")
        elif trend_1h == "SHORT" and fvg_15m == "BEARISH_FVG" and choch_5m == "BEARISH_CHOCH":
            send_telegram_message(f"🔴 *SMART MONEY: SHORT*\n📊 #{monet}\n📉 1H: SHORT\n⏳ 15M: Тест FVG\n⚡️ 5M: Слом CHOCH!")

if __name__ == "__main__":
    # Отправляем один тестовый сигнал при первом запуске
    send_telegram_message("👋 Бот успешно перенесен на Render и начинает круглосуточную проверку каждые 5 минут!")
    check_market_once()
