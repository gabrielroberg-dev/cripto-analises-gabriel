import requests
import time
import pandas as pd
import threading

# ================================
#  CONFIGURAÇÃO TELEGRAM
# ================================
BOT_TOKEN = "8348692375:AAEI_Fcuq5zBd6Il5YPZSj2XtbsXIPLMwyM"
CHAT_ID = 1793725704

DEBUG = True  # True = mostra logs no Render

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.post(url, data=payload, timeout=5)
    except Exception as e:
        if DEBUG:
            print("Erro enviando Telegram:", e)

# ================================
#  CONFIGURAÇÃO SUPORTE/RESISTÊNCIA ETH
# ================================
# Valores que você enviou
S = [2970.75, 3038.98, 2526.17, 2902.47, 2372.62, 2729.05, 2144.50]
R = [3833.01, 3237.49, 3353.29, 4213.49, 4368.80, 35000, 4057.49, 3472.96, 4774.86]

suportes = sorted(S)
resistencias = sorted(R)

# tolerância para toque = 0.3%
TOLERANCIA = 0.003

# ================================
#  PEGAR PREÇO DO COINGECKO
# ================================
def get_price():
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd",
            timeout=5
        )
        return r.json()["ethereum"]["usd"]
    except:
        return None

# ================================
#  FUNÇÕES DE ANÁLISE PRICE ACTION
# ================================
def tocou_nivel(price, nivel):
    """Retorna True se price estiver dentro da tolerância"""
    margem = nivel * TOLERANCIA
    return abs(price - nivel) <= margem

def verificar_sinal(price):
    global suportes, resistencias

    # verificar toque em suporte
    for s in suportes:
        if tocou_nivel(price, s):
            return ("COMPRA", s)

    # verificar toque em resistência
    for r in resistencias:
        if tocou_nivel(price, r):
            return ("VENDA", r)

    # verificar rompimento de resistência → vira suporte
    for r in list(resistencias):
        if price > r * (1 + TOLERANCIA):
            resistencias.remove(r)
            suportes.append(r)
            suportes = sorted(suportes)
            if DEBUG: print(f"[ROMPIMENTO] Resistência {r} virou SUPORTE")
            return ("ROMPIMENTO_RESISTENCIA", r)

    # verificar rompimento de suporte → vira resistência
    for s in list(suportes):
        if price < s * (1 - TOLERANCIA):
            suportes.remove(s)
            resistencias.append(s)
            resistencias = sorted(resistencias)
            if DEBUG: print(f"[ROMPIMENTO] Suporte {s} virou RESISTÊNCIA")
            return ("ROMPIMENTO_SUPORTE", s)

    return (None, None)

# ================================
#  LOOP PRINCIPAL DO BOT
# ================================
def run_bot():
    print("🚀 Bot de Price Action ETH iniciado!")
    ultimo_sinal = None

    while True:
        price = get_price()

        if price is None:
            if DEBUG: print("Erro ao pegar preço...")
            time.sleep(10)
            continue

        if DEBUG:
            print(f"[Preço ETH] {price}")

        tipo, nivel = verificar_sinal(price)

        if tipo and ultimo_sinal != (tipo, nivel):
            if tipo == "COMPRA":
                msg = (
                    f"🔵 *SINAL DE COMPRA - ETH*\n"
                    f"💰 Preço atual: {price}\n"
                    f"📌 Suporte tocado: {nivel}"
                )
            elif tipo == "VENDA":
                msg = (
                    f"🔴 *SINAL DE VENDA - ETH*\n"
                    f"💰 Preço atual: {price}\n"
                    f"📌 Resistência tocada: {nivel}"
                )
            elif tipo == "ROMPIMENTO_RESISTENCIA":
                msg = (
                    f"🟢 *RESISTÊNCIA ROMPIDA - ETH*\n"
                    f"💰 Preço: {price}\n"
                    f"📈 Resistência {nivel} virou SUPORTE!"
                )
            elif tipo == "ROMPIMENTO_SUPORTE":
                msg = (
                    f"🟠 *SUPORTE PERDIDO - ETH*\n"
                    f"💰 Preço: {price}\n"
                    f"📉 Suporte {nivel} virou RESISTÊNCIA!"
                )

            send_telegram(msg)
            ultimo_sinal = (tipo, nivel)

        time.sleep(30)  # Atualiza a cada 30 segundos

if __name__ == "__main__":
    run_bot()
