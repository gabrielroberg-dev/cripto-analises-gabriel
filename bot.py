import time
import requests

print("BOT ETH INICIADO 🚀")

# =====================================================
# CONFIG TELEGRAM
# =====================================================
BOT_TOKEN = "8348692375:AAEI_Fcuq5zBd6Il5YPZSj2XtbsXIPLMwyM"
CHAT_ID = "1793725704"

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
        requests.post(url, data=data)
    except Exception as e:
        print("[ERRO TELEGRAM]:", e)

# =====================================================
# PEGAR PREÇO KRAKEN
# =====================================================
def get_eth_price():
    try:
        url = "https://api.kraken.com/0/public/Ticker?pair=ETHUSDT"
        r = requests.get(url)
        data = r.json()

        key = list(data["result"].keys())[0]
        price = float(data["result"][key]["c"][0])
        return price

    except Exception as e:
        print("[ERRO] Falha ao obter preço Kraken:", e)
        return None

# =====================================================
# SUPORTES E RESISTÊNCIAS
# =====================================================
SUPORTES = [3000, 3238, 2900, 2800, 2700]
RESISTENCIAS = [3300, 3400, 3500, 3600]

def detectar_sr(preco):
    suporte = max([s for s in SUPORTES if s <= preco], default=min(SUPORTES))
    resistencia = min([r for r in RESISTENCIAS if r >= preco], default=max(RESISTENCIAS))
    return suporte, resistencia

# =====================================================
# EVITAR SPAM
# =====================================================
ultimo_sinal = None  # compra, venda, rompeu_suporte, rompeu_resistencia

# =====================================================
# LOOP PRINCIPAL
# =====================================================
while True:
    preco = get_eth_price()

    if preco:
        suporte, resistencia = detectar_sr(preco)

        print("\n=======================================")
        print(f"[ETH] Preço: {preco:.2f} USDT")
        print(f"→ Suporte mais próximo: {suporte}")
        print(f"→ Resistência mais próxima: {resistencia}")
        print("=======================================")

        # -------------------------------------------------------------
        #               🎯 TOCOU SUPORTE → SINAL DE COMPRA
        # -------------------------------------------------------------
        if preco <= suporte * 1.003 and ultimo_sinal != "compra":
            msg = (
                f"🟢 *SINAL DE COMPRA - ETH*\n\n"
                f"Preço atual: `{preco:.2f}` USDT\n"
                f"Suporte tocado: `{suporte}`\n"
                f"🛒 Possível ponto de reversão!"
            )
            send_telegram(msg)
            ultimo_sinal = "compra"

        # -------------------------------------------------------------
        #               🔴 TOCOU RESISTÊNCIA → SINAL DE VENDA
        # -------------------------------------------------------------
        elif preco >= resistencia * 0.997 and ultimo_sinal != "venda":
            msg = (
                f"🔴 *SINAL DE VENDA - ETH*\n\n"
                f"Preço atual: `{preco:.2f}` USDT\n"
                f"Resistência tocada: `{resistencia}`\n"
                f"📉 Possível topo!"
            )
            send_telegram(msg)
            ultimo_sinal = "venda"

        # -------------------------------------------------------------
        #               ⚠️ ROMPEU SUPORTE → ALERTA DE QUEDA
        # -------------------------------------------------------------
        elif preco < suporte * 0.995 and ultimo_sinal != "rompeu_suporte":
            msg = (
                f"⚠️ *ROMPIMENTO DE SUPORTE - ETH*\n\n"
                f"Preço atual: `{preco:.2f}` USDT\n"
                f"Suporte rompido: `{suporte}`\n"
                f"🚨 Pressão vendedora forte! Possível continuação da queda."
            )
            send_telegram(msg)
            ultimo_sinal = "rompeu_suporte"

        # -------------------------------------------------------------
        #          🚀 ROMPEU RESISTÊNCIA → ALERTA DE ALTA
        # -------------------------------------------------------------
        elif preco > resistencia * 1.005 and ultimo_sinal != "rompeu_resistencia":
            msg = (
                f"🚀 *ROMPIMENTO DE RESISTÊNCIA - ETH*\n\n"
                f"Preço atual: `{preco:.2f}` USDT\n"
                f"Resistência rompida: `{resistencia}`\n"
                f"🔥 Possível continuação da alta!"
            )
            send_telegram(msg)
            ultimo_sinal = "rompeu_resistencia"

        # -------------------------------------------------------------
        #          RESET quando preço volta entre suporte e resistência
        # -------------------------------------------------------------
        if suporte < preco < resistencia:
            ultimo_sinal = None

    time.sleep(5)
