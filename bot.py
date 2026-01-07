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
    except Exception as e:
        print("Erro Telegram:", e, flush=True)

# =====================================================
# PREÇO - BINANCE
# =====================================================
def get_eth_price():
    try:
        r = requests.get(
            "https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT",
            timeout=10
        ).json()
        return float(r["price"])
    except Exception as e:
        print("Erro preço:", e, flush=True)
        return None

# =====================================================
# RSI
# =====================================================
def get_rsi(period=14):
    try:
        r = requests.get(
            "https://api.binance.com/api/v3/klines?symbol=ETHUSDT&interval=5m&limit=100",
            timeout=10
        ).json()
        closes = [float(c[4]) for c in r]

        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        gains = [d for d in deltas if d > 0]
        losses = [-d for d in deltas if d < 0]

        avg_gain = sum(gains[-period:]) / period if gains else 0.001
        avg_loss = sum(losses[-period:]) / period if losses else 0.001

        rs = avg_gain / avg_loss
        return round(100 - (100 / (1 + rs)), 2)
    except Exception as e:
        print("Erro RSI:", e, flush=True)
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
# CONTROLE DE ALERTAS
# =====================================================
status = {}

def key(n, tf):
    return f"{n}_{tf}"

def ensure_status(n, tf):
    if key(n, tf) not in status:
        status[key(n, tf)] = {
            "ultimo_alerta": datetime.min
        }
    return key(n, tf)

# =====================================================
# CONFIG ASSISTENTE
# =====================================================
TOQUE_TOL = 0.003        # 0.3%
COOLDOWN = timedelta(hours=6)
HEARTBEAT = timedelta(minutes=30)
ultimo_heartbeat = datetime.now()

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

        # HEARTBEAT
        if datetime.now() - ultimo_heartbeat > HEARTBEAT:
            send_telegram("🤖 Assistente ETH ativo | Monitorando zonas técnicas")
            ultimo_heartbeat = datetime.now()

        # ================= SUPORTES =================
        for s in SUPORTES:
            n, tf = s["nivel"], s["tf"]
            k = ensure_status(n, tf)

            dist = abs(preco - n) / n

            if dist <= TOQUE_TOL:
                if datetime.now() - status[k]["ultimo_alerta"] > COOLDOWN:
                    classe = classificar_nivel("SUPORTE", tf, rsi)

                    send_telegram(
                        f"🟢 *ETH | REGIÃO DE SUPORTE ({tf})*\n\n"
                        f"📍 Preço atual: `{preco:.2f}`\n"
                        f"📉 RSI (5m): `{rsi}`\n"
                        f"🧭 Nível técnico: `{n}`\n"
                        f"📊 Força do nível: `{classe}`\n\n"
                        f"🧠 Região de decisão técnica.\n"
                        f"⚠️ Faça sua própria análise."
                    )

                    status[k]["ultimo_alerta"] = datetime.now()

        # ================= RESISTÊNCIAS =================
        for r in RESISTENCIAS:
            n, tf = r["nivel"], r["tf"]
            k = ensure_status(n, tf)

            dist = abs(preco - n) / n

            if dist <= TOQUE_TOL:
                if datetime.now() - status[k]["ultimo_alerta"] > COOLDOWN:
                    classe = classificar_nivel("RESISTENCIA", tf, rsi)

                    send_telegram(
                        f"🔴 *ETH | REGIÃO DE RESISTÊNCIA ({tf})*\n\n"
                        f"📍 Preço atual: `{preco:.2f}`\n"
                        f"📈 RSI (5m): `{rsi}`\n"
                        f"🧭 Nível técnico: `{n}`\n"
                        f"📊 Força do nível: `{classe}`\n\n"
                        f"🧠 Região de decisão técnica.\n"
                        f"⚠️ Faça sua própria análise."
                    )

                    status[k]["ultimo_alerta"] = datetime.now()

        time.sleep(5)

    except Exception as e:
        print("Erro geral:", e, flush=True)
        time.sleep(10)
