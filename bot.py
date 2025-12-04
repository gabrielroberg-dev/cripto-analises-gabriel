import requests
import time
import os

API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_SECRET_KEY")

BASE_URL = "https://fapi.binance.com"  # Binance Futures API


# ================================
#  FUNÇÕES SEGURO-CONTRA-ERROS
# ================================
def get_price():
    url = "https://api.binance.com/api/v3/ticker/price"
    params = {"symbol": "BTCUSDT"}

    try:
        r = requests.get(url, params=params, timeout=5)
        if r.status_code != 200:
            print("Erro ao buscar preço:", r.text)
            return 0

        data = r.json()

        # Proteção total
        if "price" not in data:
            print("Erro: campo 'price' ausente:", data)
            return 0

        return float(data["price"])

    except Exception as e:
        print("Erro inesperado em get_price:", e)
        return 0


def get_funding():
    url = f"{BASE_URL}/fapi/v1/fundingRate?symbol=BTCUSDT&limit=1"

    try:
        r = requests.get(url, timeout=5)
        data = r.json()

        # Deve vir como lista
        if not isinstance(data, list) or len(data) == 0:
            print("Erro no funding, resposta inválida:", data)
            return 0

        return float(data[0].get("fundingRate", 0))

    except Exception as e:
        print("Erro inesperado em get_funding:", e)
        return 0


def get_open_interest(symbol="BTCUSDT"):
    try:
        r = requests.get(f"{BASE_URL}/fapi/v1/openInterest?symbol={symbol}", timeout=5)
        data = r.json()

        return float(data.get("openInterest", 0))

    except Exception as e:
        print("Erro no open interest:", e)
        return 0


def get_liquidations(symbol="BTCUSDT"):
    url = f"{BASE_URL}/futures/data/liquidationOrders?symbol={symbol}&limit=50"

    try:
        r = requests.get(url, timeout=5)
        data = r.json()

        if not isinstance(data, list):
            print("Erro nas liquidações, resposta ruim:", data)
            return 0, 0

        longs = sum(float(x.get("price", 0)) for x in data if x.get("side") == "BUY")
        shorts = sum(float(x.get("price", 0)) for x in data if x.get("side") == "SELL")

        return longs, shorts

    except Exception as e:
        print("Erro inesperado em get_liquidations:", e)
        return 0, 0


# ================================
#  LOOP PRINCIPAL
# ================================
def run_bot():
    print("🚀 Bot iniciado com sucesso! Monitorando BTCUSDT...")

    while True:
        price = get_price()
        funding = get_funding()
        oi = get_open_interest()
        longs, shorts = get_liquidations()

        print("\n" + "=" * 40)
        print("📊 ANÁLISE AUTOMÁTICA - BTCUSDT")
        print(f"💰 Preço atual: {price}")
        print(f"📈 Funding rate: {funding}")
        print(f"📦 Open Interest: {oi}")
        print(f"🔥 Liquidação LONGS: {longs}")
        print(f"❄ Liquidação SHORTS: {shorts}")

        # Interpretação simples
        if funding > 0:
            print("🔎 Mercado tende a ALTA (funding positivo)")
        else:
            print("🔎 Mercado tende a BAIXA (funding negativo)")

        if longs > shorts:
            print("⚠️ Muito long sendo liquidado → pressão de baixa.")
        else:
            print("⚠️ Muito short sendo liquidado → pressão de alta.")

        print("=" * 40)

        time.sleep(20)  # Atualiza a cada 20s


if __name__ == "__main__":
    run_bot()
