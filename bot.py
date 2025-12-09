import requests
import time
import threading

# -----------------------------------------
# FUNÇÃO PARA PEGAR O PREÇO DO ETH (BINANCE)
# -----------------------------------------
def get_price_eth():
    try:
        url = "https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT"
        r = requests.get(url, timeout=10)

        data = r.json()

        return float(data["price"])

    except Exception as e:
        print("Erro ao obter preço:", e)
        return None


# -----------------------------------------
# ANÁLISE SIMPLES
# -----------------------------------------
def analisar_eth(price):
    suportes = [2800, 3000, 3200]
    resistencias = [3400, 3600, 3800]

    suporte_prox = max([s for s in suportes if s <= price], default=suportes[0])
    resistencia_prox = min([r for r in resistencias if r >= price], default=resistencias[-1])

    print(f"[ETH] Preço atual: {price}")
    print(f" → Suporte mais próximo: {suporte_prox}")
    print(f" → Resistência mais próxima: {resistencia_prox}")
    print("-" * 50)


# -----------------------------------------
# LOOP DO BOT
# -----------------------------------------
def loop_eth():
    print("BOT ETH INICIADO 🚀")

    while True:
        price = get_price_eth()

        if price:
            analisar_eth(price)

        time.sleep(5)  # Pode ser 5s, Binance aguenta


# -----------------------------------------
# INICIAR
# -----------------------------------------
if __name__ == "__main__":
    t = threading.Thread(target=loop_eth)
    t.start()

    while True:
        time.sleep(1)
