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
# RSI
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
# CLASSIFICAÇÃO RSI
# =====================================================
def classificar_rsi(rsi, tipo):
    if tipo == "compra":
        if rsi <= 30:
            return "🟢 *Oportunidade MUITO forte (RSI sobrevendido)*"
        elif rsi <= 40:
            return "🟢 *Oportunidade mediana (RSI baixo)*"
        else:
            return "ℹ️ RSI neutro"

    if tipo == "venda":
        if rsi >= 70:
            return "🔴 *Oportunidade MUITO forte (RSI sobrecomprado)*"
        elif rsi >= 60:
            return "🔴 *Oportunidade mediana (RSI alto)*"
        else:
            return "ℹ️ RSI neutro"

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
    print(f"→ Suporte: {suporte}")
    print(f"→ Resistência: {resistencia}")
    print("=======================================")

    # TOLERÂNCIA mínima para considerar TOQUE real
    toque_tolerancia = 0.0005  # 0.05%

    # =====================================================
    # ROMPIMENTO PARA CIMA
    # =====================================================
    if preco > resistencia * 1.005:
        if resistencia in dynamic_resistances:
            dynamic_resistances.remove(resistencia)
            dynamic_supports.add(resistencia)

        if ultimo_sinal != "rompeu_resistencia":
            send_telegram(
                f"🚀 *ROMPIMENTO DE RESISTÊNCIA - ETH*\n\n"
                f"Preço: `{preco:.2f}`\n"
                f"Novo suporte: `{resistencia}`\n"
                f"RSI: `{rsi}`\n"
                f"🔥 Alta confirmada!"
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
                f"⚠️ *ROMPIMENTO DE SUPORTE - ETH*\n\n"
                f"Preço: `{preco:.2f}`\n"
                f"Novo nível virou resistência: `{suporte}`\n"
                f"RSI: `{rsi}`\n"
                f"🚨 Baixa confirmada."
            )
            ultimo_sinal = "rompeu_suporte"

    # =====================================================
    # TOQUE NO SUPORTE (EXATO)
    # =====================================================
    elif abs(preco - suporte) <= suporte * toque_tolerancia and ultimo_sinal != "compra":
        classificacao = classificar_rsi(rsi, "compra")
        send_telegram(
            f"🟢 *TOQUE EXATO NO SUPORTE - ETH*\n\n"
            f"Preço: `{preco:.2f}`\n"
            f"SUPORTE: `{suporte}`\n"
            f"RSI: `{rsi}`\n\n"
            f"{classificacao}"
        )
        ultimo_sinal = "compra"

    # =====================================================
    # TOQUE NA RESISTÊNCIA (EXATO)
    # =====================================================
    elif abs(preco - resistencia) <= resistencia * toque_tolerancia and ultimo_sinal != "venda":
        classificacao = classificar_rsi(rsi, "venda")
        send_telegram(
            f"🔴 *TOQUE EXATO NA RESISTÊNCIA - ETH*\n\n"
            f"Preço: `{preco:.2f}`\n"
            f"RESISTÊNCIA: `{resistencia}`\n"
            f"RSI: `{rsi}`\n\n"
            f"{classificacao}"
        )
        ultimo_sinal = "venda"

    # RESET de sinal apenas quando voltar ao meio
    if suporte < preco < resistencia:
        ultimo_sinal = None

    time.sleep(5)
