import requests
import time
import os

API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_SECRET_KEY")

BASE_URL = "https://fapi.binance.com"  # Binance Futures API


def get_price():
    url = "https://api.binance.com/api/v3/ticker/price"
    params = {"symbol": "BTCUSDT"}

    r = requests.get(url, params=params)
    data = r.json()

    return float(data.get("price", 0))


def get_funding():
    try:
        url = "https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT&limit=1"
        r = requests.get(url)
        data = r.json()
        return float(data[0].get("fundingRate", 0))
    except Exception as e:
        print("Erro no funding:", e)
        return 0


def get_open_interest(symbol="BTCUSDT"):
    try:
        r = requests.get(f"{BASE_URL}/fapi/v1/openInterest?symbol={symbol}")
        return float(r.json().get("openInterest", 0))
    except:
        return 0


def get_liquidations(symbol="BTCUSDT"):
    try:
        r = requests.get(f"{BASE_URL}/futures/data/liquidationOrders?symbol={symbol}&limit=50")
        data = r.json()
        longs = sum(float(x.get("price", 0)) for x in data if x.get("side") == "BUY")
        shorts = sum(float(x.get("price", 0)) for x in data if x.get("side") == "SELL")
        return longs, shorts
    except Exception as e:
        print("Erro nas liquidações:", e)
        return 0, 0


def run_bot():
    while True:
        price = get_price()
        funding = get_funding()
        oi = get_open_interest()
        longs, shorts = get_liquidations()

        print("=" * 40)
        print("📊 ANÁLISE AUTOMÁTICA - BTCUSDT")
        print(f"💰 Preço atual: {price}")
        print(f"📈 Funding rate: {funding}")
        print(f"📦 Open Interest: {oi}")
        print(f"🔥 Liquidação LONGS: {longs}")
        print(f"❄ Liquidação SHORTS: {shorts}")

        # Interpretação simples
        if funding > 0:
            print("🔎 Mercado tende a alta (funding positivo)")
        else:
            print("🔎 Mercado tende a baixa (funding negativo)")

        if longs > shorts:
            print("⚠️ Muito long sendo liquidado → possível queda.")
        else:
            print("⚠️ Muito short sendo liquidado → possível alta.")

        print("=" * 40)
        time.sleep(20)  # atualiza a cada 20s


if __name__ == "__main__":
    run_bot()
