import requests
import time
import threading

# ================================
#  CONFIGURAÇÃO TELEGRAM
# ================================
BOT_TOKEN = "8348692375:AAEI_Fcuq5zBd6Il5YPZSj2XtbsXIPLMwyM"
CHAT_ID = 1793725704

DEBUG = True  # True para logs detalhados

def send_telegram(message):
    """Envia mensagem para o Telegram"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.post(url, data=payload, timeout=5)
    except Exception as e:
        if DEBUG:
            print("Erro enviando Telegram:", e)

# ================================
#  PEGAR PREÇO NA BINANCE (ESTÁVEL)
# ================================
def get_price():
    try:
        r = requests.get(
            "https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT",
            timeout=5
        )
        return float(r.json()["price"])
    except Exception as e:
        if DEBUG:
            print("Erro ao pegar preço:", e)
        return None

# ================================
#  SUPORTES E RESISTÊNCIAS (ETH)
# ================================
suportes_resistencias = {
    "4h": {"S":[2970.75], "R":[3833.01]},
    "1d": {"S":[3038.98, 2526.17, 2526.17], "R":[3237.49, 3353.29, 4213.49]},
    "1w": {"S":[2902.47, 2372.62], "R":[4368.80, 35000]},
    "1m": {"S":[2729.05, 2144.50, 0.0], "R":[4057.49, 3472.96, 4774.86]}
}

# ================================
#   LÓGICA SIMPLIFICADA DE SINAIS
# ================================
def check_levels(price, timeframe):
    levels = suportes_resistencias[timeframe]
    S = sorted(levels["S"])
    R = sorted(levels["R"])

    suporte_mais_proximo = max([s for s in S if s <= price], default=S[0])
    resistencia_mais_proxima = min([r for r in R if r >= price], default=R[0])

    sinal = None

    # → Bateu no suporte = COMPRA
    if abs(price - suporte_mais_proximo) <= (price * 0.003):
        sinal = f"🟢 *COMPRA* — Preço tocou o suporte {suporte_mais_proximo}"

    # → Bateu na resistência = VENDA
    if abs(price - resistencia_mais_proxima) <= (price * 0.003):
        sinal = f"🔴 *VENDA* — Preço tocou a resistência {resistencia_mais_proxima}"

    # → Rompeu resistência → vira suporte
    if price > resistencia_mais_proxima:
        levels["S"].append(resistencia_mais_proxima)
        levels["R"].remove(resistencia_mais_proxima)
        sinal = f"🟢 *ROMPIMENTO DE ALTA!* Resistência {resistencia_mais_proxima} virou suporte."

    # → Rompeu suporte → vira resistência
    if price < suporte_mais_proximo:
        levels["R"].append(suporte_mais_proximo)
        levels["S"].remove(suporte_mais_proximo)
        sinal = f"🔴 *ROMPIMENTO DE BAIXA!* Suporte {suporte_mais_proximo} virou resistência."

    return sinal, suporte_mais_proximo, resistencia_mais_proxima


# ================================
#   THREAD PARA CADA TIMEFRAME
# ================================
def run_timeframe(tf, last_signals):
    while True:
        price = get_price()
        if price is None:
            time.sleep(5)
            continue

        if DEBUG:
            print(f"[Preço ETH] {price}")

        sinal, S, R = check_levels(price, tf)

        if sinal:
            key = f"{tf}_{sinal}"

            if last_signals.get(key) != sinal:
                message = (
                    f"📊 *Sinal ETH/USDT — Timeframe {tf}*\n"
                    f"💰 Preço: {price}\n"
                    f"📉 Suporte mais próximo: {S}\n"
                    f"📈 Resistência mais próxima: {R}\n\n"
                    f"{sinal}"
                )
                send_telegram(message)
                last_signals[key] = sinal

        time.sleep(20)  # a cada 20 segundos para ficar mais responsivo


# ================================
#   BOT PRINCIPAL
# ================================
def run_bot():
    print("🚀 BOT VIP ETH iniciado!")
    last_signals = {}

    threads = []
    for tf in ["4h", "1d", "1w", "1m"]:
        t = threading.Thread(target=run_timeframe, args=(tf, last_signals))
        t.daemon = True
        t.start()
        threads.append(t)

    while True:
        if DEBUG:
            print(f"[{time.strftime('%H:%M:%S')}] Rodando threads ETH...")
        time.sleep(120)

if __name__ == "__main__":
    run_bot()
