import time
import requests

API_KEY = "COLOQUE_SUA_API_KEY_AQUI"  # Binance API KEY se for colocar no futuro

# ===== BUSCAR PREÇO DA BINANCE (SEM LIMITE) =====
def get_eth_price():
    try:
        url = "https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT"
        response = requests.get(url)
        data = response.json()
        return float(data["price"])
    except Exception as e:
        print("[ERRO] Falha ao obter preço:", e)
        return None

# ===== SUPORTE E RESISTÊNCIA FIXOS (por enquanto) =====
SUPORTES = [3000, 2900, 2800, 2700]
RESISTENCIAS = [3300, 3400, 3500, 3600]

def detectar_sr(preco):
    suporte = max([s for s in SUPORTES if s <= preco], default=SUPORTES[-1])
    resistencia = min([r for r in RESISTENCIAS if r >= preco], default=RESISTENCIAS[0])
    return suporte, resistencia

print("BOT ETH INICIADO 🚀")

while True:
    preco = get_eth_price()

    if preco:
        suporte, resistencia = detectar_sr(preco)

        print("\n=======================================")
        print(f"[ETH] Preço: {preco:.2f} USDT")
        print(f"→ Suporte mais próximo: {suporte}")
        print(f"→ Resistência mais próxima: {resistencia}")
        print("=======================================")

    time.sleep(10)
