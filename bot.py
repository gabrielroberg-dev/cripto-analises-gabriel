import time
import requests
from datetime import datetime, timedelta

print("ASSISTENTE CRIPTO (KRAKEN) INICIADO 🤖🚀", flush=True)

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
# PREÇO ETH - KRAKEN
# =====================================================
def get_eth_price():
    try:
        r = requests.get(
            "https://api.kraken.com/0/public/Ticker?pair=ETHUSD",
            timeout=10
        ).json()

        result = r.get("result", {})
        pair = list(result.values())[0]
        return float(pair["c"][0])
    except:
        return None

# =====================================================
# RSI ETH - KRAKEN (5m)
# =====================================================
def get_rsi(period=14):
    try:
        r = requests.get(
            "https://api.kraken.com/0/public/OHLC?pair=ETHUSD&interval=5",
            timeout=10
        ).json()

        result = r.get("result", {})
        key = [k for k in result.keys() if k != "last"][0]
        candles = result[key]

        closes = [float(c[4]) for c in candles]

        if len(closes) < period + 1:
            return None

        gains, losses = [], []

        for i in range(1, period + 1):
            delta = closes[-i] - closes[-i-1]
            if delta >= 0:
                gains.append(delta)
            else:
                losses.append(abs(delta))

        avg_gain = sum(gains) / period if gains else 0.001
        avg_loss = sum(losses) / period if losses else 0.001

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return round(rsi, 2)
    except:
        return None

# =====================================================
# CLASSIFICAÇÃO DE FORÇA
# =====================================================
def classificar(tipo, tf, rsi):
    score = {"1W":4,"1D":3,"4H":2,"1H":1}.get(tf,0)

    if tipo == "SUPORTE":
        score += 3 if rsi <= 30 else 1 if rsi <= 40 else 0
    else:
        score += 3 if rsi >= 70 else 1 if rsi >= 60 else 0

    if score >= 7: return "A+"
    if score >= 4: return "B"
    return "C"

# =====================================================
# NÍVEIS TÉCNICOS
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
# CONTROLE
# =====================================================
status = {}
def key(n, tf): return f"{n}_{tf}"
def ensure(n, tf):
    if key(n, tf) not in status:
        status[key(n, tf)] = datetime.min
    return key(n, tf)

TOQUE = 0.003
COOLDOWN = timedelta(hours=6)
HEARTBEAT = timedelta(minutes=30)
last_heartbeat = datetime.now()

# =====================================================
# LOOP PRINCIPAL
# =====================================================
while True:
    try:
        preco = get_eth_price()
        rsi = get_rsi()

        if preco is None or rsi is None:
            time.sleep(15)
            continue

        if datetime.now() - last_heartbeat > HEARTBEAT:
            send_telegram("🤖 Assistente ETH ativo | Kraken | Monitorando zonas técnicas")
            last_heartbeat = datetime.now()

        for s in SUPORTES:
            n, tf = s["nivel"], s["tf"]
            k = ensure(n, tf)

            if abs(preco - n) / n <= TOQUE:
                if datetime.now() - status[k] > COOLDOWN:
                    send_telegram(
                        f"🟢 *ETH | SUPORTE ({tf})*\n\n"
                        f"Preço: `{preco:.2f}`\n"
                        f"RSI: `{rsi}`\n"
                        f"Nível: `{n}`\n"
                        f"Força: `{classificar('SUPORTE', tf, rsi)}`\n\n"
                        f"⚠️ Não é recomendação. Faça sua análise."
                    )
                    status[k] = datetime.now()

        for r in RESISTENCIAS:
            n, tf = r["nivel"], r["tf"]
            k = ensure(n, tf)

            if abs(preco - n) / n <= TOQUE:
                if datetime.now() - status[k] > COOLDOWN:
                    send_telegram(
                        f"🔴 *ETH | RESISTÊNCIA ({tf})*\n\n"
                        f"Preço: `{preco:.2f}`\n"
                        f"RSI: `{rsi}`\n"
                        f"Nível: `{n}`\n"
                        f"Força: `{classificar('RESISTENCIA', tf, rsi)}`\n\n"
                        f"⚠️ Não é recomendação. Faça sua análise."
                    )
                    status[k] = datetime.now()

        time.sleep(15)

    except:
        time.sleep(20)
