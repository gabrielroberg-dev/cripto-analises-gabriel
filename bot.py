import requests
import time
import threading

# =====================================================
#  CONFIG TELEGRAM
# =====================================================
BOT_TOKEN = "8348692375:AAEI_Fcuq5zBd6Il5YPZSj2XtbsXIPLMwyM"
CHAT_ID = 1793725704
DEBUG = True


def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
        requests.post(url, data=data, timeout=5)
    except Exception as e:
        print("Erro Telegram:", e)


# =====================================================
#   SUPORTES E RESISTÊNCIAS — ETH
# =====================================================
SR = {
    "ETH": {
        "4h": {"S": [2970.75], "R": [3833.01]},
        "1d": {"S": [3038.98, 2526.17], "R": [3237.49, 3353.29, 4213.49]},
        "1w": {"S": [2902.47, 2372.62], "R": [4368.80, 35000]},
        "1m": {"S": [2729.05, 2144.50, 0.0], "R": [4057.49, 3472.96, 4774.86]},
    }
}


# =====================================================
#   PEGAR PREÇO — APENAS COINGECKO (SEM LIMITAR)
# =====================================================
def get_price():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd"

    try:
        r = requests.get(url, timeout=6)
        if r.status_code == 200:
            data = r.json()
            return float(data["ethereum"]["usd"])
        else:
            if DEBUG:
                print("[CoinGecko] Status:", r.status_code, r.text[:100])
    except Exception as e:
        if DEBUG:
            print("Erro ao consultar preço:", e)

    return None


# =====================================================
#   ANALISAR SUPORTES / RESISTÊNCIAS
# =====================================================
def analisar_sr(symbol, timeframe, last_state):

    price = get_price()
    if price is None:
        print("Falha ao obter preço.")
        return

    niveis = SR[symbol][timeframe]

    suportes = sorted(niveis["S"])
    resistencias = sorted(niveis["R"])

    if not suportes or not resistencias:
        print("Erro: lista vazia de S ou R")
        return

    # nível mais próximo abaixo do preço
    s_prox = None
    for s in suportes:
        if s <= price:
            s_prox = s
    if s_prox is None:
        s_prox = suportes[0]

    # nível mais próximo acima do preço
    r_prox = None
    for r in resistencias:
        if r >= price:
            r_prox = r
            break
    if r_prox is None:
        r_prox = resistencias[-1]

    key = f"{symbol}_{timeframe}"

    # =====================
    #  BATEU SUPORTE
    # =====================
    if abs(price - s_prox) <= 0.30:
        if last_state.get(key) != f"SUPORTE_{s_prox}":
            send_telegram(
                f"🟢 *COMPRA* — ETH tocou o suporte *{s_prox}*\n💵 Preço atual: *{price}*"
            )
            last_state[key] = f"SUPORTE_{s_prox}"
        return

    # =====================
    #  BATEU RESISTÊNCIA
    # =====================
    if abs(price - r_prox) <= 0.30:
        if last_state.get(key) != f"RESISTENCIA_{r_prox}":
            send_telegram(
                f"🔴 *VENDA* — ETH tocou a resistência *{r_prox}*\n💵 Preço atual: *{price}*"
            )
            last_state[key] = f"RESISTENCIA_{r_prox}"
        return

    # =====================
    #  ROMPIMENTO PARA CIMA
    # =====================
    if price > r_prox:
        if last_state.get(key) != f"ROMPEU_CIMA_{r_prox}":
            send_telegram(
                f"🚀 *ROMPIMENTO PRA CIMA!* — resistência *{r_prox}* virou SUPORTE\n💵 Preço: {price}"
            )
            niveis["S"].append(r_prox)
            niveis["R"].remove(r_prox)
            last_state[key] = f"ROMPEU_CIMA_{r_prox}"
        return

    # =====================
    #  ROMPIMENTO PARA BAIXO
    # =====================
    if price < s_prox:
        if last_state.get(key) != f"ROMPEU_BAIXO_{s_prox}":
            send_telegram(
                f"⚠️ *ROMPIMENTO PRA BAIXO!* — suporte *{s_prox}* virou RESISTÊNCIA\n💵 Preço: {price}"
            )
            niveis["R"].append(s_prox)
            niveis["S"].remove(s_prox)
            last_state[key] = f"ROMPEU_BAIXO_{s_prox}"
        return

    if DEBUG:
        print(f"[{symbol} {timeframe}] Preço verificado: {price}")


# =====================================================
#   THREAD ETH
# =====================================================
def loop_eth(last_state):
    while True:
        for tf in ["4h", "1d", "1w", "1m"]:
            analisar_sr("ETH", tf, last_state)
        time.sleep(15)  # consulta a cada 15s


# =====================================================
#   MAIN
# =====================================================
def run_bot():
    print("BOT INICIADO 🚀")
    last_state = {}

    t = threading.Thread(target=loop_eth, args=(last_state,))
    t.daemon = True
    t.start()

    while True:
        time.sleep(60)


if __name__ == "__main__":
    run_bot()
