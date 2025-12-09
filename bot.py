import time
import requests

print("BOT ETH INICIADO 🚀")

# ===== BUSCAR PREÇO DA BITGET (SEM LIMITE, SEM API KEY) =====
def get_eth_price():
    try:
        url = "https://api.bitget.com/api/spot/v1/market/tickers?symbol=ETHUSDT"
        response = requests.get(url)
        data = response.json()

        # Bitget retorna uma lista dentro de "data"
        return float(data["data"][0]["close"])
    except Exception as e:
        print("[ERRO] Falha ao obter preço da Bitget:", e)
        return None

# ===== SUPORTE E RESISTÊNCIA FIXOS (por enquanto) =====
SUPORTES = [3000, 2900, 2800, 2700]
RESISTENCIAS = [3300, 3400, 3500, 3600]

def detectar_sr(preco):
    suporte = max([s for s in SUPORTES if s <= preco], default=SUPORTES[-1])
    resistencia = min([r for r in RESISTENCIAS if r >= preco], default=RESISTENCIAS[0])
    return suporte, resistencia

while True:
    preco = get_eth_price()

    if preco:
        suporte, resistencia = detectar_sr(preco)

        print("\n=======================================")
        print(f"[ETH] Preço: {preco:.2f} USDT")
        print(f"→ Suporte mais próximo: {suporte}")
        print(f"→ Resistência mais próxima: {resistencia}")
        print("=======================================")

    time.sleep(5)
