import requests
import time
import threading

# ============================================
#  CONFIG TELEGRAM
# ============================================
BOT_TOKEN = "8348692375:AAEI_Fcuq5zBd6Il5YPZSj2XtbsXIPLMwyM"
CHAT_ID = 1793725704
DEBUG = True


def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.post(url, data=payload, timeout=5)
    except Exception as e:
        if DEBUG:
            print("Erro Telegram:", e)


# ============================================
#  SUPORTES E RESISTÊNCIAS ETH
# ============================================
SR = {
    "ETH": {
        "4h": {"S": [2970.75], "R": [3833.01]},
        "1d": {"S": [3038.98, 2526.17, 2526.17], "R": [3237.49, 3353.29, 4213.49]},
        "1w": {"S": [2902.47, 2372.62], "R": [4368.80, 35000]},
        "1m": {"S": [2729.05, 2144.50, 0.0], "R": [4057.49, 3472.96, 4774.86]},
    }
}


# ============================================
#  FUNÇÃO DE PREÇO — 100% GARANTIDA
# ============================================
def get_price():

    # 1 — DEXSCREENER (FUNCIONA SEMPRE)
    try:
        r = requests.get(
            "https://api.dexscreener.com/latest/dex/search?q=eth",
            timeout=5
        )
        data = r.json()

        if "pairs" in data and len(data["pairs"]) > 0:
            best = max(data["pairs"], key=lambda x: x.get("liquidity", {}).get("usd", 0))
            return float(best["priceUsd"])
    except Exception as e:
        if DEBUG:
            print("[DexScreener] erro:", e)

    # 2 — FALLBACK EM CASO EXTREMO
    try:
        r = requests.get(
            "https://api.coinpaprika.com/v1/tickers/eth-ethereum",
            timeout=5
        )
        data = r.json()
        return float(data["quotes"]["USD"]["price"])
    except Exception as e:
        if DEBUG:
            print("[Paprika] erro:", e)

    if DEBUG:
        print("🔥 Falha ao pegar preço!")
    return None


# ============================================
#  ANALISAR SUPORTE E RESISTÊNCIA
# ============================================
def analisar_sr(symbol, timeframe, last_state):
    price = get_price()

    if price is None:
        if DEBUG:
            print("Erro ao pegar preço")
        return

    niveis = SR[symbol][timeframe]
    suportes = sorted(niveis["S"])
    resistencias = sorted(niveis["R"])

    s_prox = max([s for s in suportes if s <= price], default=suportes[0])
    r_prox = min([r for r in resistencias if r >= price], default=resistencias[0])

    key = f"{symbol}_{timeframe}"

    # ============ CONDIÇÕES ============

    # BATEU SUPORTE → COMPRA
    if abs(price - s_prox) <= 0.3:
        sinal = f"🟢 *COMPRA* — ETH bateu o suporte {s_prox}\n💵 Preço: {price}"
        if last_state.get(key) != f"SUPORTE_{s_prox}":
            send_telegram(sinal)
            last_state[key] = f"SUPORTE_{s_prox}"
        return

    # BATEU RESISTÊNCIA → VENDA
    if abs(price - r_prox) <= 0.3:
        sinal = f"🔴 *VENDA* — ETH bateu a resistência {r_prox}\n💵 Preço: {price}"
        if last_state.get(key) != f"RESISTENCIA_{r_prox}":
            send_telegram(sinal)
            last_state[key] = f"RESISTENCIA_{r_prox}"
        return

    # ROMPEU PARA CIMA
    if price > r_prox:
        sinal = f"🚀 *ROMPIMENTO PRA CIMA!* — resistência {r_prox} virou SUPORTE\n💵 Preço: {price}"
        if last_state.get(key) != f"ROMPEU_CIMA_{r_prox}":
            send_telegram(sinal)
            niveis["S"].append(r_prox)
            niveis["R"].remove(r_prox)
            last_state[key] = f"ROMPEU_CIMA_{r_prox}"
        return

    # ROMPEU PARA BAIXO
    if price < s_prox:
        sinal = f"⚠️ *ROMPIMENTO PRA BAIXO!* — suporte {s_prox} virou RESISTÊNCIA\n💵 Preço: {price}"
        if last_state.get(key) != f"ROMPEU_BAIXO_{s_prox}":
            send_telegram(sinal)
            niveis["R"].append(s_prox)
            niveis["S"].remove(s_prox)
            last_state[key] = f"ROMPEU_BAIXO_{s_prox}"
        return

    if DEBUG:
        print(f"[{symbol} {timeframe}] Preço OK | {price}")


# ============================================
#  THREAD ETH
# ============================================
def loop_eth(last_state):
    while True:
        for tf in ["4h", "1d", "1w", "1m"]:
            analisar_sr("ETH", tf, last_state)
        time.sleep(20)


# ============================================
#  BOT PRINCIPAL
# ============================================
def run_bot():
    print("🚀 Bot Ultimate SR INICIADO!")
    last_state = {}

    t = threading.Thread(target=loop_eth, args=(last_state,))
    t.daemon = True
    t.start()

    while True:
        if DEBUG:
            print("[RUNNING] Bot ativo...")
        time.sleep(60)


if __name__ == "__main__":
    run_bot()
