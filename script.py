
import ccxt
import pandas as pd
import time
from ta.momentum import RSIIndicator
from ta.trend import MACD, ADXIndicator
import telegram
from telegram.error import TelegramError
import asyncio
from pycoingecko import CoinGeckoAPI
import os

# Configuración desde variables de entorno o por defecto
TIMEFRAMES = ['4h', '1d']
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
ADX_PERIOD = 14
LIMIT = 200
TOP_COINS = 100

# Telegram
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

# Inicializa Bybit
exchange = ccxt.bybit({
    'enableRateLimit': True,
    'options': {
        'defaultType': 'spot',
    }
})

# Telegram bot
bot = telegram.Bot(token=TELEGRAM_TOKEN)

# CoinGecko
cg = CoinGeckoAPI()

async def send_telegram_message(message):
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        print(f"Enviado a Telegram: {message}")
    except TelegramError as e:
        print(f"Error al enviar mensaje: {e}")

def get_top_coins(top_n):
    try:
        coins = cg.get_coins_markets(vs_currency='usd', order='market_cap_desc', per_page=top_n, page=1)
        return [coin['symbol'].upper() for coin in coins]
    except Exception as e:
        print(f"Error al obtener top monedas: {e}")
        return []

def fetch_indicators(symbol, timeframe):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=LIMIT)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['rsi'] = RSIIndicator(close=df['close'], window=RSI_PERIOD).rsi()
        macd = MACD(close=df['close'], window_fast=MACD_FAST, window_slow=MACD_SLOW, window_sign=MACD_SIGNAL)
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        adx = ADXIndicator(high=df['high'], low=df['low'], close=df['close'], window=ADX_PERIOD)
        df['adx'] = adx.adx()

        last = df.iloc[-1]
        prev = df.iloc[-2]
        return {
            'rsi': last['rsi'],
            'macd': last['macd'],
            'macd_signal': last['macd_signal'],
            'prev_macd': prev['macd'],
            'prev_macd_signal': prev['macd_signal'],
            'adx': last['adx']
        }
    except Exception as e:
        print(f"Error con {symbol} [{timeframe}]: {e}")
        return None

async def scan_market():
    top_coins = get_top_coins(TOP_COINS)
    if not top_coins:
        return

    markets = exchange.load_markets()
    usdt_pairs = [s for s in markets if '/USDT' in s and ':' not in s and s.split('/')[0] in top_coins]

    for tf in TIMEFRAMES:
        for symbol in usdt_pairs:
            indicators = fetch_indicators(symbol, tf)
            if indicators is None:
                continue

            rsi_signal = None
            if indicators['rsi'] < RSI_OVERSOLD:
                rsi_signal = f"🔻 {symbol} ({tf}) RSI {indicators['rsi']:.2f} (Sobrevendido)"
            elif indicators['rsi'] > RSI_OVERBOUGHT:
                rsi_signal = f"🔺 {symbol} ({tf}) RSI {indicators['rsi']:.2f} (Sobrecomprado)"

            macd_signal = None
            if indicators['rsi'] < RSI_OVERSOLD and indicators['macd'] < 0 and indicators['macd'] > indicators['macd_signal'] and indicators['prev_macd'] <= indicators['prev_macd_signal']:
                macd_signal = "+ MACD Valle rojo (Cruce alcista)"
            elif indicators['rsi'] > RSI_OVERBOUGHT and indicators['macd'] > 0 and indicators['macd'] < indicators['macd_signal'] and indicators['prev_macd'] >= indicators['prev_macd_signal']:
                macd_signal = "+ MACD Pico rojo (Cruce bajista)"

            adx_info = f" | ADX: {indicators['adx']:.2f}"

            if rsi_signal:
                message = rsi_signal
                if macd_signal:
                    message += f" {macd_signal}"
                message += adx_info
                await send_telegram_message(message)
            time.sleep(exchange.rateLimit / 1000)

async def main_loop():
    while True:
        print("⏳ Ejecutando escaneo de mercado...")
        await scan_market()
        print("⏲️ Esperando 2 horas para próxima ejecución...
")
        await asyncio.sleep(2 * 60 * 60)

if __name__ == "__main__":
    asyncio.run(main_loop())
