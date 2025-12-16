import time
import requests

print("BOT ETH INICIADO 🚀")

# =====================================================
# CONFIG TELEGRAM
# =====================================================
BOT_TOKEN = "SEU_TOKEN"
CHAT_ID = "SEU_CHAT_ID"

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
# SUPORTES / RESISTÊNCIAS COM TIMEFRAME
# =====================================================
SUPORTES = [
    {"nivel": 3000, "tf": "1D"},
    {"nivel": 3238, "tf": "4H"},
    {"nivel": 2900, "tf": "1D"},
    {"nivel": 2800, "tf": "1W"},
    {"nivel": 2700, "tf": "1W"},
]

RESISTENCIAS = [
    {"nivel": 3300, "tf": "4H"},
    {"nivel": 3354, "tf": "1D"},
    {"nivel": 3400, "tf": "1D"},
    {"nivel": 3500, "tf": "1W"},
    {"nivel": 3600, "tf": "1W"},
]

# =====================================================
# ESTADO DOS NÍVEIS (ANTI-SPAM)
# =====================================================
status_niveis = {}

def key(nivel, tf):
    return f"{nivel}_{tf}"

for item in SUPORTES + RESISTENCIAS:
    status_niveis[key(item["nivel"], item["tf"])] = {
        "aproximacao": False,
        "toque": False,
        "rompido": False
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

    toque_tolerancia = 0.0005
    aprox_min = 0.002
    aprox_max = 0.007
    reset_dist = 0.03

    # -------------------------------------------------
    # SUPORTES
    # -------------------------------------------------
    for s in SUPORTES[:]:

        nivel = s["nivel"]
        tf = s["tf"]
        k = key(nivel, tf)
        dist = abs(preco - nivel) / nivel

        if dist > reset_dist:
            status_niveis[k]["aproximacao"] = False
            status_niveis[k]["toque"] = False

        if aprox_min <= dist <= aprox_max and not status_niveis[k]["aproximacao"]:
            send_telegram(
                f"🟡 *Aproximando do SUPORTE ({tf}) - ETH*\n\n"
                f"Preço: `{preco:.2f}`\nSuporte: `{nivel}`\nRSI: `{rsi}`"
            )
            status_niveis[k]["aproximacao"] = True

        if dist <= toque_tolerancia and not status_niveis[k]["toque"]:
            send_telegram(
                f"🟢 *TOQUE EXATO NO SUPORTE ({tf}) - ETH*\n\n"
                f"Preço: `{preco:.2f}`\nSuporte: `{nivel}`\nRSI: `{rsi}`"
            )
            status_niveis[k]["toque"] = True

        if preco < nivel * 0.999 and not status_niveis[k]["rompido"]:
            send_telegram(
                f"❌ *SUPORTE ROMPIDO ({tf}) - ETH*\n\n"
                f"Preço: `{preco:.2f}`\nNível: `{nivel}`\nRSI: `{rsi}`\n\n"
                f"➡️ Agora virou *RESISTÊNCIA*"
            )
            SUPORTES.remove(s)
            RESISTENCIAS.append(s)
            status_niveis[k]["rompido"] = True

    # -------------------------------------------------
    # RESISTÊNCIAS
    # -------------------------------------------------
    for r in RESISTENCIAS[:]:

        nivel = r["nivel"]
        tf = r["tf"]
        k = key(nivel, tf)
        dist = abs(preco - nivel) / nivel

        if dist > reset_dist:
            status_niveis[k]["aproximacao"] = False
            status_niveis[k]["toque"] = False

        if aprox_min <= dist <= aprox_max and not status_niveis[k]["aproximacao"]:
            send_telegram(
                f"🟠 *Aproximando da RESISTÊNCIA ({tf}) - ETH*\n\n"
                f"Preço: `{preco:.2f}`\nResistência: `{nivel}`\nRSI: `{rsi}`"
            )
            status_niveis[k]["aproximacao"] = True

        if dist <= toque_tolerancia and not status_niveis[k]["toque"]:
            send_telegram(
                f"🔴 *TOQUE EXATO NA RESISTÊNCIA ({tf}) - ETH*\n\n"
                f"Preço: `{preco:.2f}`\nResistência: `{nivel}`\nRSI: `{rsi}`"
            )
            status_niveis[k]["toque"] = True

        if preco > nivel * 1.001 and not status_niveis[k]["rompido"]:
            send_telegram(
                f"✅ *RESISTÊNCIA ROMPIDA ({tf}) - ETH*\n\n"
                f"Preço: `{preco:.2f}`\nNível: `{nivel}`\nRSI: `{rsi}`\n\n"
                f"➡️ Agora virou *SUPORTE*"
            )
            RESISTENCIAS.remove(r)
            SUPORTES.append(r)
            status_niveis[k]["rompido"] = True

    time.sleep(5)
