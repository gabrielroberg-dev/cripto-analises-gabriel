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
    except:
        pass

# =====================================================
# PEGAR PREÇO KRAKEN
# =====================================================
def get_eth_price():
    try:
        url = "https://api.kraken.com/0/public/Ticker?pair=ETHUSDT"
        r = requests.get(url)
        data = r.json()
        key = list(data["result"].keys())[0]
        return float(data["result"][key]["c"][0])
    except:
        return None

# =====================================================
# SUPORTES E RESISTÊNCIAS (BASE)
# =====================================================
SUPORTES = [3000, 3238, 2900, 2800, 2700]
RESISTENCIAS = [3300, 3354, 3400, 3500, 3600]

# Listas dinamicamente ajustadas após rompimentos
dynamic_supports = set(SUPORTES)
dynamic_resistances = set(RESISTENCIAS)

# =====================================================
# DETECTAR SR CONSIDERANDO FLIP
# =====================================================
def detectar_sr(preco):
    suporte = max([s for s in dynamic_supports if s <= preco], default=min(dynamic_supports))
    resistencia = min([r for r in dynamic_resistances if r >= preco], default=max(dynamic_resistances))
    return suporte, resistencia

# =====================================================
# CONTROLE PARA EVITAR SPAM
# =====================================================
ultimo_sinal = None

# =====================================================
# LOOP PRINCIPAL
# =====================================================
while True:
    preco = get_eth_price()
    if not preco:
        time.sleep(5)
        continue

    # calcular niveis mais próximos agora com flip aplicado
    suporte, resistencia = detectar_sr(preco)

    print("\n=======================================")
    print(f"[ETH] Preço: {preco:.2f} USDT")
    print(f"→ Suporte atual: {suporte}")
    print(f"→ Resistência atual: {resistencia}")
    print("=======================================")

    # LÓGICA: ROMPIMENTO PARA CIMA (resistência vira suporte)
    if preco > resistencia * 1.005:
        if resistencia in dynamic_resistances:
            dynamic_resistances.remove(resistencia)
            dynamic_supports.add(resistencia)

        if ultimo_sinal != "rompeu_resistencia":
            send_telegram(
                f"🚀 *Rompimento de Resistência - ETH*\n\n"
                f"Preço atual: `{preco:.2f}` USDT\n"
                f"Nível rompido virou SUPORTE: `{resistencia}`\n"
                f"🔥 Estrutura de alta continuada."
            )
            ultimo_sinal = "rompeu_resistencia"

    # LÓGICA: ROMPIMENTO PARA BAIXO (suporte vira resistência)
    elif preco < suporte * 0.995:
        if suporte in dynamic_supports:
            dynamic_supports.remove(suporte)
            dynamic_resistances.add(suporte)

        if ultimo_sinal != "rompeu_suporte":
            send_telegram(
                f"⚠️ *Rompimento de Suporte - ETH*\n\n"
                f"Preço atual: `{preco:.2f}` USDT\n"
                f"Nível rompido virou RESISTÊNCIA: `{suporte}`\n"
                f"🚨 Estrutura de baixa continua."
            )
            ultimo_sinal = "rompeu_suporte"

    # TOCOU SUPORTE → possível compra
    elif preco <= suporte * 1.003 and ultimo_sinal != "compra":
        send_telegram(
            f"🟢 *Possível Oportunidade de Compra - ETH*\n\n"
            f"Preço atual: `{preco:.2f}`\n"
            f"SUPORTE tocado: `{suporte}`\n\n"
            f"📌 Região importante de possível reversão."
        )
        ultimo_sinal = "compra"

    # TOCOU RESISTÊNCIA → possível venda
    elif preco >= resistencia * 0.997 and ultimo_sinal != "venda":
        send_telegram(
            f"🔴 *Possível Oportunidade de Venda - ETH*\n\n"
            f"Preço atual: `{preco:.2f}`\n"
            f"RESISTÊNCIA tocada: `{resistencia}`\n\n"
            f"📌 Região potencial de topo."
        )
        ultimo_sinal = "venda"

    # RESET quando preço volta ao meio da zona
    if suporte < preco < resistencia:
        ultimo_sinal = None

    time.sleep(5)
