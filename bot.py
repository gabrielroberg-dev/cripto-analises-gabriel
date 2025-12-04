import requests
import time
import os

API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_SECRET_KEY")

BASE_URL = "https://fapi.binance.com"  # Binance Futures API

# ================================
#  CONFIGURAÇÃO TELEGRAM
# ================================
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # ou coloque seu token direto
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")      # ID do chat do Telegram

def send_telegram(message):
    """Envia mensagem para o Telegram"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.post(url, data=payload, timeout=5)
    except Exception as e:
        print("Erro enviando Telegram:", e)

# ================================
#  FUNÇÕES DE DADOS
# ================================
def get_btc_price():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        response = requests.get(url, timeout=5)
        data = response.json()
        return data["bitcoin"]["usd"]
    except Exception as e:
        print("Erro CoinGecko:", e)

    # Fallback Binance
    try:
        url_binance = f"{BASE_URL}/fapi/v1/ticker/price?symbol=BTCUSDT"
        r = requests.get(url_binance, timeout=5)
        data = r.json()
        return float(data.get("price", 0))
    except Exception as e:
        print("Erro Binance:", e)
        return 0


def get_funding():
    try:
        url = f"{BASE_URL}/fapi/v1/fundingRate?symbol=BTCUSDT&limit=1"
        r = requests.get(url, timeout=5)
        data = r.json()
        if isinstance(data, list) and len(data) > 0:
            return float(data[0].get("fundingRate", 0))
        return 0
    except Exception as e:
        print("Erro funding:", e)
        return 0


def get_open_interest(symbol="BTCUSDT"):
    try:
        r = requests.get(f"{BASE_URL}/fapi/v1/openInterest?symbol={symbol}", timeout=5)
        data = r.json()
        return float(data.get("openInterest", 0))
    except Exception as e:
        print("Erro open interest:", e)
        return 0


def get_liquidations(symbol="BTCUSDT"):
    try:
        url = f"{BASE_URL}/futures/data/liquidationOrders?symbol={symbol}&limit=50"
        r = requests.get(url, timeout=5)
        data = r.json()
        if not isinstance(data, list):
            return 0, 0

        longs = sum(float(x.get("price", 0)) for x in data if x.get("side") == "BUY")
        shorts = sum(float(x.get("price", 0)) for x in data if x.get("side") == "SELL")
        return longs, shorts
    except Exception as e:
        print("Erro liquidations:", e)
        return 0, 0

# ================================
#  ANÁLISE DE TENDÊNCIA
# ================================
def analyze_market(price, funding, longs, shorts):
    trend = "NEUTRO"
    if funding > 0:
        trend = "ALTA 📈"
    elif funding < 0:
        trend = "BAIXA 📉"

    liquidation_alert = ""
    if longs > shorts:
        liquidation_alert = "⚠️ Muito long sendo liquidado → pressão de baixa."
    elif shorts > longs:
        liquidation_alert = "⚠️ Muito short sendo liquidado → pressão de alta."

    return trend, liquidation_alert

# ================================
#  LOOP PRINCIPAL
# ================================
def run_bot():
    print("🚀 Bot iniciado com sucesso! Monitorando BTCUSDT...")

    last_trend = None
    last_liquidation_alert = None

    while True:
        price = get_btc_price()
        funding = get_funding()
        oi = get_open_interest()
        longs, shorts = get_liquidations()

        trend, liquidation_alert = analyze_market(price, funding, longs, shorts)

        # Só envia mensagem se houver mudança significativa
        if trend != last_trend or liquidation_alert != last_liquidation_alert:
            message = (
                f"📊 *ANÁLISE AUTOMÁTICA - BTCUSDT*\n"
                f"💰 Preço atual: {price} USD\n"
                f"📈 Funding rate: {funding}\n"
                f"📦 Open Interest: {oi}\n"
                f"🔥 Liquidação LONGS: {longs}\n"
                f"❄ Liquidação SHORTS: {shorts}\n"
                f"🔎 Tendência: {trend}\n"
            )
            if liquidation_alert:
                message += f"{liquidation_alert}\n"

            send_telegram(message)
            print(message)
            print("=" * 40)

            # Atualiza o estado
            last_trend = trend
            last_liquidation_alert = liquidation_alert

        time.sleep(20)  # Atualiza a cada 20s


if __name__ == "__main__":
    run_bot()
