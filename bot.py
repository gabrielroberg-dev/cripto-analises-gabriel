import time
import requests
from datetime import datetime, timedelta

print("ASSISTENTE CRIPTO ETH INICIADO 🤖🚀", flush=True)

# =====================================================
# CONFIG TELEGRAM
# =====================================================
BOT_TOKEN = "SEU_TOKEN"
CHAT_ID = "SEU_CHAT_ID"

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(
            url,
            data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"},
            timeout=10
        )
    except:
        pass

# =====================================================
# PREÇO - CRYPTOCOMPARE
# =====================================================
def get_eth_price():
    try:
        r = requests.get(
            "https://min-api.cryptocompare.com/data/price?fsym=ETH&tsyms=USD",
            timeout=10
        ).json()

        if isinstance(r, dict) and "USD" in r:
            return float(r["USD"])
        return None
    except:
        return None

# =====================================================
# RSI - CRYPTOCOMPARE (5m)
# =====================================================
def get_rsi(period=14):
    try:
        r = requests.get(
            "https://min-api.cryptocompare.com/data/v2/histominute?fsym=ETH&tsym=USD&limit=200",
            timeout=10
        ).json()

        if "Data" not in r or "Data" not in r["Data"]:
            return None

        candles = r["Data"]["Data"]
        closes = [c["close"] for c in candles if c["close"] > 0]

        if len(closes) < period + 1:
            return None

        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        gains = [d for d in deltas if d > 0]
        losses = [-d for d in deltas if d < 0]

        avg_gain = sum(gains[-period:]) / period if gains else 0.001
        avg_loss = sum(losses[-period:]) / period if losses else 0.001

        rs = avg_gain / avg_loss
        return round(100 - (100 / (1 + rs)), 2)
    except:
        return None

# =====================================================
# CLASSIFICAÇÃO DO NÍVEL
# =====================================================
def classificar_nivel(tipo, tf, rsi):
    score = {"1W":4,"1D":3,"4H":2,"1H":1}.get(tf,0)

    if tipo == "SUPORTE":
        score += 3 if rsi <= 30 else 1 if rsi <= 40 else 0
    else:
        score += 3 if rsi >= 70 else 1 if rsi >= 60 else 0

    if score >= 7: return "A+"
    if score >= 4: return "B"
    return "C"

# =====================================================
# NÍVEIS
# =====================================================
SUPORTES = [
    {"nivel":3000,"tf":"1D"},
    {"nivel":3238,"tf":"4H"},
    {"nivel":2800,"tf":"1W"},
]

RESISTENCIAS = [
    {"nivel":3300,"tf":"4H"},
    {"nivel":3500,"tf":"1W"},
]

# =====================================================
# CONTROLE DE ALERTA
# =====================================================
status = {}

def key(n, tf):
    return f"{n}_{tf}"

def ensure_status(n, tf):
    if key(n, tf) not in status:
        status[key(n, tf)] = {"ultimo": datetime.min}
    return key(n, tf)

TOQUE_TOL = 0.003
COOLDOWN = timedelta(hours=6)
HEARTBEAT = timedelta(minutes=30)
ultimo_heartbeat = datetime.now()

# =====================================================
# LOOP
# =====================================================
while True:
    try:
        preco = get_eth_price()
        rsi = get_rsi()

        if preco is None or rsi is None:
            time.sleep(15)
            continue

        if datetime.now() - ultimo_heartbeat > HEARTBEAT:
            send_telegram("🤖 Assistente ETH ativo | Monitorando zonas técnicas")
            ultimo_heartbeat = datetime.now()

        for s in SUPORTES:
            n, tf = s["nivel"], s["tf"]
            k = ensure_status(n, tf)

            if abs(preco - n) / n <= TOQUE_TOL:
                if datetime.now() - status[k]["ultimo"] > COOLDOWN:
                    classe = classificar_nivel("SUPORTE", tf, rsi)
                    send_telegram(
                        f"🟢 *ETH | SUPORTE ({tf})*\n\n"
                        f"Preço: `{preco:.2f}`\n"
                        f"RSI: `{rsi}`\n"
                        f"Nível: `{n}`\n"
                        f"Força: `{classe}`\n\n"
                        f"⚠️ Faça sua própria análise."
                    )
                    status[k]["ultimo"] = datetime.now()

        for r in RESISTENCIAS:
            n, tf = r["nivel"], r["tf"]
            k = ensure_status(n, tf)

            if abs(preco - n) / n <= TOQUE_TOL:
                if datetime.now() - status[k]["ultimo"] > COOLDOWN:
                    classe = classificar_nivel("RESISTENCIA", tf, rsi)
                    send_telegram(
                        f"🔴 *ETH | RESISTÊNCIA ({tf})*\n\n"
                        f"Preço: `{preco:.2f}`\n"
                        f"RSI: `{rsi}`\n"
                        f"Nível: `{n}`\n"
                        f"Força: `{classe}`\n\n"
                        f"⚠️ Faça sua própria análise."
                    )
                    status[k]["ultimo"] = datetime.now()

        time.sleep(15)

    except:
        time.sleep(20)
