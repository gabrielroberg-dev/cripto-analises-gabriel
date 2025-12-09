import requests
import time

BOT_TOKEN = "8348692375:AAEI_Fcuq5zBd6Il5YPZSj2XtbsXIPLMwyM"
CHAT_ID = 1793725704
DEBUG = True


def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.post(url, data=payload, timeout=5)
    except Exception as e:
        print("Erro Telegram:", e)


# ========================
# SUPORTES / RESISTÊNCIAS
# ========================
SR = {
    "S": [2970.75, 3038.98, 2526.17, 2902.47, 2372.62, 2729.05, 2144.50],
    "R": [3833.01, 3237.49, 3353.29, 4213.49, 4368.80, 35000, 4057.49, 3472.96, 4774.86],
}


# ========================
# PREÇO (SEM BINANCE)
# ========================
def get_price():
    url = "https://api.coinbase.com/v2/prices/ETH-USD/spot"

    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            return float(data["data"]["amount"])
        else:
            print("[Coinbase] Status:", r.status_code)
    except Exception as e:
        print("[Coinbase] Erro:", e)

    return None


# ========================
# LÓGICA DO BOT
# ========================
def analisar(preco, last_state):
    suportes = sorted(SR["S"])
    resistencias = sorted(SR["R"])

    s_prox = max([s for s in suportes if s <= preco], default=None)
    r_prox = min([r for r in resistencias if r >= preco], default=None)

    # Sem níveis válidos
    if s_prox is None or r_prox is None:
        print("⚠ Sem níveis SR válidos.")
        return

    print(f"[ETH] Preço: {preco} | S: {s_prox} | R: {r_prox}")

    # BATEU SUPORTE
    if abs(preco - s_prox) <= 0.3:
        if last_state != f"S_{s_prox}":
            send_telegram(f"🟢 *COMPRA* no suporte {s_prox}\nPreço: {preco}")
            last_state = f"S_{s_prox}"

    # BATEU RESISTÊNCIA
    elif abs(preco - r_prox) <= 0.3:
        if last_state != f"R_{r_prox}":
            send_telegram(f"🔴 *VENDA* na resistência {r_prox}\nPreço: {preco}")
            last_state = f"R_{r_prox}"

    return last_state


# ========================
# LOOP PRINCIPAL — COMPATÍVEL COM RENDER
# ========================
def main():
    print("BOT INICIADO 🚀")
    last_state = None

    while True:
        preco = get_price()

        if preco:
            last_state = analisar(preco, last_state)
        else:
            print("❌ Falha ao pegar preço.")

        time.sleep(20)


if __name__ == "__main__":
    main()
