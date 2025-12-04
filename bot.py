import requests
import time
import os

API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_SECRET_KEY")

BASE_URL = "https://fapi.binance.com"  # Binance Futures API


def get_price(symbol="BTCUSDT"):
    r = requests.get(f"{BASE_URL}/fapi/v1/ticker/price?symbol={symbol}")
    return float(r.json()["price"])


def get_funding(symbol="BTCUSDT"):
    r = requests.get(f"{BASE_URL}/fapi/v1/fundingRate?symbol={symbol}")
    return float(r.json()[-1]["fundingRate"])


def get_open_interest(symbol="BTCUSDT"):
    r = requests.get(f"{BASE_URL}/fapi/v1/openInterest?symbol={symbol}")
    return float(r.json()["openInterest"])


def get_liquidations(symbol="BTCUSDT"):
    r = requests.get(f"{BASE_URL}/futures/data/liquidationOrders?symbol={symbol}&limit=50")
    data = r.json()
    longs = sum(float(x["price"]) for x in data if x["side"] == "BUY")
    shorts = sum(float(x["price"]) for x in data if x["side"] == "SELL")
    return longs, shorts


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
