import requests
import time
import threading

# -----------------------------------------
# FUNÇÃO PARA PEGAR O PREÇO DO ETH
# -----------------------------------------
def get_price_eth():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": "ethereum",
            "vs_currencies": "usd"
        }
        r = requests.get(url, params=params, timeout=10)

        if r.status_code == 429:
            print("[CoinGecko] ❌ Rate limit! Aguardando 60 segundos...")
            time.sleep(60)
            return None

        data = r.json()
        return data["ethereum"]["usd"]

    except Exception as e:
        print("Erro ao obter preço:", e)
        return None


# -----------------------------------------
# ANÁLISE SIMPLES (SUPORTE / RESISTÊNCIA)
# -----------------------------------------
def analisar_eth(price):
    # Apenas EXEMPLO — pode ajustar depois
    suportes = [2800, 3000, 3200]
    resistencias = [3400, 3600, 3800]

    suporte_prox = max([s for s in suportes if s <= price], default=suportes[0])
    resistencia_prox = min([r for r in resistencias if r >= price], default=resistencias[-1])

    print(f"[ETH] Preço atual: {price}")
    print(f" → Suporte mais próximo: {suporte_prox}")
    print(f" → Resistência mais próxima: {resistencia_prox}")
    print("-" * 50)


# -----------------------------------------
# LOOP PRINCIPAL DO BOT
# -----------------------------------------
def loop_eth():
    print("BOT ETH INICIADO 🚀")

    while True:
        price = get_price_eth()

        if price:
            analisar_eth(price)

        time.sleep(120)  # Consulta a cada 2 minutos


# -----------------------------------------
# INICIAR BOT
# -----------------------------------------
if __name__ == "__main__":
    t = threading.Thread(target=loop_eth)
    t.start()

    # Manter o processo vivo no Render
    while True:
        time.sleep(1)
