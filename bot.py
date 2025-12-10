import time
import requests
import statistics

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
# KRAKEN PRICE
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
# RSI (USANDO KRAKEN - CANDLES 5 MIN)
# =====================================================
def get_rsi(period=14):
    try:
        url = "https://api.kraken.com/0/public/OHLC?pair=ETHUSDT&interval=5"
        r = requests.get(url).json()
        key = list(r["result"].keys())[0]
        candles = r["result"][key]

        closes = [float(c[4]) for c in candles]

        deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
        gains = [d for d in deltas if d > 0]
        losses = [-d for d in deltas if d < 0]

        avg_gain = (sum(gains[-period:]) / period) if len(gains) >= period else 0.001
        avg_loss = (sum(losses[-period:]) / period) if len(losses) >= period else 0.001

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return round(rsi, 2)
    except:
        return None

# =====================================================
# SUPORTES E RESISTÊNCIAS
# =====================================================
SUPORTES = [3000, 3238, 2900, 2800, 2700]
RESISTENCIAS = [3300, 3354, 3400, 3500, 3600]

dynamic_supports = set(SUPORTES)
dynamic_resistances = set(RESISTENCIAS)

def detectar_sr(preco):
    suporte = max([s for s in dynamic_supports if s <= preco], default=min(dynamic_supports))
    resistencia = min([r for r in dynamic_resistances if r >= preco], default=max(dynamic_resistances))
    return suporte, resistencia

ultimo_sinal = None

# =====================================================
# LOOP PRINCIPAL
# =====================================================
while True:
    preco = get_eth_price()
    rsi = get_rsi()

    if not preco or not rsi:
        time.sleep(5)
        continue

    suporte, resistencia = detectar_sr(preco)

    print("\n=======================================")
    print(f"[ETH] Preço: {preco:.2f} USDT | RSI: {rsi}")
    print(f"→ Suporte atual: {suporte}")
    print(f"→ Resistência atual: {resistencia}")
    print("=======================================")

    # =====================================================
    # APROXIMAÇÃO (3% de distância)
    # =====================================================
    if abs(preco - suporte) <= suporte * 0.01 and ultimo_sinal != "aprox_suporte":
        send_telegram(
            f"🟡 Aproximando do SUPORTE - ETH\n\n"
            f"Preço: {preco:.2f}\n"
            f"Suporte: {suporte}\n"
            f"RSI: {rsi}\n\n"
            f"📍 Atenção: possível ponto de reversão."
        )
        ultimo_sinal = "aprox_suporte"

    if abs(preco - resistencia) <= resistencia * 0.01 and ultimo_sinal != "aprox_resistencia":
        send_telegram(
            f"🟠 Aproximando da RESISTÊNCIA - ETH\n\n"
            f"Preço: {preco:.2f}\n"
            f"Resistência: {resistencia}\n"
            f"RSI: {rsi}\n\n"
            f"📍 Possível topo se RSI estiver alto."
        )
        ultimo_sinal = "aprox_resistencia"

    # =====================================================
    # ROMPIMENTO PARA CIMA
    # =====================================================
    if preco > resistencia * 1.005:
        if resistencia in dynamic_resistances:
            dynamic_resistances.remove(resistencia)
            dynamic_supports.add(resistencia)

        if ultimo_sinal != "rompeu_resistencia":
            send_telegram(
                f"🚀 **ROMPIMENTO DE RESISTÊNCIA - ETH**\n\n"
                f"Preço: {preco:.2f}\n"
                f"Nível rompido virou SUPORTE: {resistencia}\n"
                f"RSI: {rsi}\n"
                f"🔥 Estrutura de alta confirmada."
            )
            ultimo_sinal = "rompeu_resistencia"

    # =====================================================
    # ROMPIMENTO PARA BAIXO
    # =====================================================
    elif preco < suporte * 0.995:
        if suporte in dynamic_supports:
            dynamic_supports.remove(suporte)
            dynamic_resistances.add(suporte)

        if ultimo_sinal != "rompeu_suporte":
            send_telegram(
                f"⚠️ **ROMPIMENTO DE SUPORTE - ETH**\n\n"
                f"Preço: {preco:.2f}\n"
                f"Nível rompido virou RESISTÊNCIA: {suporte}\n"
                f"RSI: {rsi}\n"
                f"🚨 Estrutura de baixa confirmada."
            )
            ultimo_sinal = "rompeu_suporte"

    # =====================================================
    # TOQUE NO SUPORTE
    # =====================================================
    elif preco <= suporte * 1.003 and ultimo_sinal != "compra":
        send_telegram(
            f"🟢 **TOQUE NO SUPORTE - ETH**\n\n"
            f"Preço: {preco:.2f}\n"
            f"Suporte: {suporte}\n"
            f"RSI: {rsi}\n"
            f"📌 Região ideal para possível compra."
        )
        ultimo_sinal = "compra"

    # =====================================================
    # TOQUE NA RESISTÊNCIA
    # =====================================================
    elif preco >= resistencia * 0.997 and ultimo_sinal != "venda":
        send_telegram(
            f"🔴 **TOQUE NA RESISTÊNCIA - ETH**\n\n"
            f"Preço: {preco:.2f}\n"
            f"Resistência: {resistencia}\n"
            f"RSI: {rsi}\n"
            f"📌 Possível ponto de venda."
        )
        ultimo_sinal = "venda"

    # RESET
    if suporte < preco < resistencia:
        ultimo_sinal = None

    time.sleep(5)
