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
# FUNÇÕES DE MERCADO
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
# ESTADO DE ALERTAS (ANTI-SPAM REAL)
# =====================================================
alertas_enviados = {
    "aprox_suporte": False,
    "aprox_resistencia": False,
    "toque_suporte": False,
    "toque_resistencia": False,
    "rompeu_suporte": False,
    "rompeu_resistencia": False
}

def reset_alertas():
    for k in alertas_enviados:
        alertas_enviados[k] = False

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

    print(f"\nPreço: {preco:.2f} | RSI: {rsi} | Suporte: {suporte} | Resistência: {resistencia}")

    toque_tolerancia = 0.0005   # 0.05%
    aprox_min = 0.002           # 0.2%
    aprox_max = 0.007           # 0.7%

    dist_suporte = abs(preco - suporte) / suporte
    dist_resistencia = abs(preco - resistencia) / resistencia

    # =====================================================
    # APROXIMAÇÃO DO SUPORTE
    # =====================================================
    if aprox_min <= dist_suporte <= aprox_max and not alertas_enviados["aprox_suporte"]:
        send_telegram(
            f"🟡 *Aproximando do SUPORTE - ETH*\n\n"
            f"Preço: `{preco:.2f}`\n"
            f"Suporte: `{suporte}`\n"
            f"RSI: `{rsi}`"
        )
        alertas_enviados["aprox_suporte"] = True

    # =====================================================
    # APROXIMAÇÃO DA RESISTÊNCIA
    # =====================================================
    if aprox_min <= dist_resistencia <= aprox_max and not alertas_enviados["aprox_resistencia"]:
        send_telegram(
            f"🟠 *Aproximando da RESISTÊNCIA - ETH*\n\n"
            f"Preço: `{preco:.2f}`\n"
            f"Resistência: `{resistencia}`\n"
            f"RSI: `{rsi}`"
        )
        alertas_enviados["aprox_resistencia"] = True

    # =====================================================
    # POSSÍVEL OPORTUNIDADE DE COMPRA
    # =====================================================
    if dist_suporte <= toque_tolerancia and not alertas_enviados["toque_suporte"]:
        classificacao = classificar_rsi(rsi, "compra")
        send_telegram(
            f"🟢 *TOQUE EXATO NO SUPORTE - ETH*\n\n"
            f"Preço: `{preco:.2f}`\n"
            f"Suporte: `{suporte}`\n"
            f"RSI: `{rsi}`\n\n"
            f"{classificacao}"
        )
        alertas_enviados["toque_suporte"] = True

    # =====================================================
    # POSSÍVEL OPORTUNIDADE DE VENDA
    # =====================================================
    if dist_resistencia <= toque_tolerancia and not alertas_enviados["toque_resistencia"]:
        classificacao = classificar_rsi(rsi, "venda")
        send_telegram(
            f"🔴 *TOQUE EXATO NA RESISTÊNCIA - ETH*\n\n"
            f"Preço: `{preco:.2f}`\n"
            f"Resistência: `{resistencia}`\n"
            f"RSI: `{rsi}`\n\n"
            f"{classificacao}"
        )
        alertas_enviados["toque_resistencia"] = True

    # =====================================================
    # RESET INTELIGENTE (sem spam)
    # =====================================================
    if dist_suporte > aprox_max and dist_resistencia > aprox_max:
        reset_alertas()

    time.sleep(5)
