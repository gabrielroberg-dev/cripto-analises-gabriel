import time
import requests

print("BOT ETH INICIADO 🚀", flush=True)

# =====================================================
# CONFIG TELEGRAM
# =====================================================
BOT_TOKEN = "SEU_TOKEN"
CHAT_ID = "SEU_CHAT_ID"

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print("Erro Telegram:", e, flush=True)

# =====================================================
# PREÇO
# =====================================================
def get_eth_price():
    try:
        url = "https://api.kraken.com/0/public/Ticker?pair=ETHUSDT"
        r = requests.get(url, timeout=10).json()
        key = list(r["result"].keys())[0]
        return float(r["result"][key]["c"][0])
    except Exception as e:
        print("Erro preço:", e, flush=True)
        return None

# =====================================================
# RSI
# =====================================================
def get_rsi(period=14):
    try:
        url = "https://api.kraken.com/0/public/OHLC?pair=ETHUSDT&interval=5"
        r = requests.get(url, timeout=10).json()
        key = list(r["result"].keys())[0]
        candles = r["result"][key]
        closes = [float(c[4]) for c in candles]

        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        gains = [d for d in deltas if d > 0]
        losses = [-d for d in deltas if d < 0]

        avg_gain = sum(gains[-period:]) / period if len(gains) >= period else 0.001
        avg_loss = sum(losses[-period:]) / period if len(losses) >= period else 0.001

        rs = avg_gain / avg_loss
        return round(100 - (100 / (1 + rs)), 2)
    except Exception as e:
        print("Erro RSI:", e, flush=True)
        return None

# =====================================================
# CLASSIFICAÇÃO A+ / B / C
# =====================================================
def classificar_entrada(tipo, tf, rsi):
    score = 0

    if tf == "1W":
        score += 4
    elif tf == "1D":
        score += 3
    elif tf == "4H":
        score += 2
    elif tf == "1H":
        score += 1

    if tipo == "compra":
        if rsi <= 30:
            score += 3
        elif rsi <= 40:
            score += 1
    else:
        if rsi >= 70:
            score += 3
        elif rsi >= 60:
            score += 1

    if score >= 7:
        return "🟢 **ENTRADA A+**"
    elif score >= 4:
        return "🟡 **ENTRADA B**"
    else:
        return "⚪ **ENTRADA C**"

# =====================================================
# NÍVEIS
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
# ESTADO ANTI-SPAM
# =====================================================
status = {}

def key(n, tf):
    return f"{n}_{tf}"

def ensure_status(n, tf):
    k = key(n, tf)
    if k not in status:
        status[k] = {"toque": False, "rompido": False}
    return k

# =====================================================
# LOOP PRINCIPAL
# =====================================================
while True:
    try:
        preco = get_eth_price()
        rsi = get_rsi()

        if not preco or not rsi:
            time.sleep(5)
            continue

        print(f"Preço: {preco:.2f} | RSI: {rsi}", flush=True)

        toque_tol = 0.0005
        reset_dist = 0.03

        # ---------------- SUPORTES ----------------
        for s in SUPORTES[:]:
            n, tf = s["nivel"], s["tf"]
            k = ensure_status(n, tf)
            dist = abs(preco - n) / n

            if dist > reset_dist:
                status[k]["toque"] = False

            if dist <= toque_tol and not status[k]["toque"]:
                nota = classificar_entrada("compra", tf, rsi)
                send_telegram(
                    f"{nota}\n\n"
                    f"🟢 *TOQUE NO SUPORTE ({tf})*\n"
                    f"📍 `{n}` | 💰 `{preco:.2f}`\n"
                    f"📉 RSI: `{rsi}`"
                )
                status[k]["toque"] = True

            if preco < n * 0.999 and not status[k]["rompido"]:
                send_telegram(
                    f"❌ *SUPORTE ROMPIDO ({tf})*\n"
                    f"Nível `{n}` virou *RESISTÊNCIA*"
                )
                SUPORTES.remove(s)
                RESISTENCIAS.append(s)
                status[k]["rompido"] = True

        # ---------------- RESISTÊNCIAS ----------------
        for r in RESISTENCIAS[:]:
            n, tf = r["nivel"], r["tf"]
            k = ensure_status(n, tf)
            dist = abs(preco - n) / n

            if dist > reset_dist:
                status[k]["toque"] = False

            if dist <= toque_tol and not status[k]["toque"]:
                nota = classificar_entrada("venda", tf, rsi)
                send_telegram(
                    f"{nota}\n\n"
                    f"🔴 *TOQUE NA RESISTÊNCIA ({tf})*\n"
                    f"📍 `{n}` | 💰 `{preco:.2f}`\n"
                    f"📈 RSI: `{rsi}`"
                )
                status[k]["toque"] = True

            if preco > n * 1.001 and not status[k]["rompido"]:
                send_telegram(
                    f"✅ *RESISTÊNCIA ROMPIDA ({tf})*\n"
                    f"Nível `{n}` virou *SUPORTE*"
                )
                RESISTENCIAS.remove(r)
                SUPORTES.append(r)
                status[k]["rompido"] = True

        time.sleep(5)

    except Exception as e:
        print("Erro geral:", e, flush=True)
        time.sleep(10)
