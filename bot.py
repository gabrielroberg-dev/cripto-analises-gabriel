import time
import requests

print("BOT ETH INICIADO 🚀")

def get_eth_price():
    try:
        url = "https://api.kraken.com/0/public/Ticker?pair=ETHUSDT"
        r = requests.get(url)
        data = r.json()

        # Kraken: price está em data["result"]["XETHZUSD"]["c"][0]
        key = list(data["result"].keys())[0]
        price = float(data["result"][key]["c"][0])
        return price

    except Exception as e:
        print("[ERRO] Falha ao obter preço Kraken:", e)
        return None

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
