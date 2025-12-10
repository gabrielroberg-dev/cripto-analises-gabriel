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
# PREÇO
# =====================================================
def get_eth_price():
    try:
        url = "https://api.kraken.com/0/public/Ticker?pair=ETHUSDT"
        data = requests.get(url).json()
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

        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        gains  = [d for d in deltas if d > 0]
        losses = [-d for d in deltas if d < 0]

        avg_gain = (sum(gains[-period:])  / period) if len(gains)  >= period else 0.001
        avg_loss = (sum(losses[-period:]) / period) if len(losses) >= period else 0.001

        rs = avg_gain / avg_loss
        return round(100 - (100 / (1 + rs)), 2)
    except:
        return None

# =====================================================
# SUPORTES / RESISTÊNCIAS
# =====================================================
SUPORTES = [3000, 3238, 2900, 2800, 2700]
RESISTENCIAS = [3300, 3354, 3400, 3500, 3600]

# =====================================================
# ESTADO PARA CADA NÍVEL (ANTI-SPAM)
# =====================================================
status_niveis = {}

for s in SUPORTES + RESISTENCIAS:
    status_niveis[s] = {
        "aproximacao": False,
        "toque": False
    }

# =====================================================
# LOOP PRINCIPAL
# =====================================================
while True:

    preco = get_eth_price()
    rsi = get_rsi()
    if not preco or not rsi:
        time.sleep(5)
        continue

    print(f"\nPreço: {preco:.2f} | RSI: {rsi}")

    toque_tolerancia = 0.0005   # 0.05%
    aprox_min = 0.002           # 0.2%
    aprox_max = 0.007           # 0.7%
    reset_dist = 0.03           # 3%

    # -------------------------------------------------
    # SUPORTES
    # -------------------------------------------------
    for s in SUPORTES:
        dist = abs(preco - s) / s

        # Reset por afastamento > 3%
        if dist > reset_dist:
            status_niveis[s]["aproximacao"] = False
            status_niveis[s]["toque"] = False

        # Aproximação 0.2–0.7%
        if aprox_min <= dist <= aprox_max and not status_niveis[s]["aproximacao"]:
            send_telegram(
                f"🟡 *Aproximando do SUPORTE - ETH*\n\n"
                f"Preço: `{preco:.2f}`\nSuporte: `{s}`\nRSI: `{rsi}`"
            )
            status_niveis[s]["aproximacao"] = True

        # Toque exato
        if dist <= toque_tolerancia and not status_niveis[s]["toque"]:
            send_telegram(
                f"🟢 *TOQUE EXATO NO SUPORTE - ETH*\n\n"
                f"Preço: `{preco:.2f}`\nSuporte: `{s}`\nRSI: `{rsi}`"
            )
            status_niveis[s]["toque"] = True

    # -------------------------------------------------
    # RESISTÊNCIAS
    # -------------------------------------------------
    for r in RESISTENCIAS:
        dist = abs(preco - r) / r

        # Reset por afastamento > 3%
        if dist > reset_dist:
            status_niveis[r]["aproximacao"] = False
            status_niveis[r]["toque"] = False

        # Aproximação 0.2–0.7%
        if aprox_min <= dist <= aprox_max and not status_niveis[r]["aproximacao"]:
            send_telegram(
                f"🟠 *Aproximando da RESISTÊNCIA - ETH*\n\n"
                f"Preço: `{preco:.2f}`\nResistência: `{r}`\nRSI: `{rsi}`"
            )
            status_niveis[r]["aproximacao"] = True

        # Toque exato
        if dist <= toque_tolerancia and not status_niveis[r]["toque"]:
            send_telegram(
                f"🔴 *TOQUE EXATO NA RESISTÊNCIA - ETH*\n\n"
                f"Preço: `{preco:.2f}`\nResistência: `{r}`\nRSI: `{rsi}`"
            )
            status_niveis[r]["toque"] = True

    time.sleep(5)
