import time
import requests
from datetime import datetime, timedelta

print("BOT ETH INICIADO 🚀", flush=True)

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
# PREÇO
# =====================================================
def get_eth_price():
    try:
        r = requests.get(
            "https://api.kraken.com/0/public/Ticker?pair=ETHUSDT",
            timeout=10
        ).json()
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
        r = requests.get(
            "https://api.kraken.com/0/public/OHLC?pair=ETHUSDT&interval=5",
            timeout=10
        ).json()
        key = list(r["result"].keys())[0]
        closes = [float(c[4]) for c in r["result"][key]]

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
# CLASSIFICAÇÃO
# =====================================================
def classificar_entrada(tipo, tf, rsi):
    score = {"1W":4,"1D":3,"4H":2,"1H":1}.get(tf,0)

    if tipo == "compra":
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
# STATUS + HISTÓRICO
# =====================================================
status = {}
historico = []

def key(n, tf):
    return f"{n}_{tf}"

def ensure_status(n, tf):
    if key(n, tf) not in status:
        status[key(n, tf)] = {"toque": False}
    return key(n, tf)

# =====================================================
# RELATÓRIO
# =====================================================
def enviar_relatorio():
    wins = sum(1 for s in historico if s["resultado"] == "WIN")
    loss = sum(1 for s in historico if s["resultado"] == "LOSS")
    total = wins + loss
    taxa = (wins / total) * 100 if total > 0 else 0

    send_telegram(
        f"📊 *RANKING ATUAL DO BOT*\n\n"
        f"✅ Wins: `{wins}`\n"
        f"❌ Loss: `{loss}`\n"
        f"🎯 Taxa de Acerto: `{taxa:.2f}%`"
    )

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

        # -------- AVALIA SETUPS ABERTOS --------
        for s in historico:
            if s["resultado"] != "PENDENTE":
                continue

            # expira após 12h
            if datetime.now() - s["hora"] > timedelta(hours=12):
                s["resultado"] = "NEUTRO"
                continue

            if s["tipo"] == "compra":
                if preco >= s["entrada"] * 1.012:
                    s["resultado"] = "WIN"
                elif preco <= s["entrada"] * 0.992:
                    s["resultado"] = "LOSS"
            else:
                if preco <= s["entrada"] * 0.988:
                    s["resultado"] = "WIN"
                elif preco >= s["entrada"] * 1.008:
                    s["resultado"] = "LOSS"

            if s["resultado"] in ["WIN", "LOSS"]:
                send_telegram(
                    f"{'✅' if s['resultado']=='WIN' else '❌'} *RESULTADO DO SETUP*\n\n"
                    f"{s['tipo'].upper()} `{s['classe']}` ({s['tf']})\n"
                    f"Entrada: `{s['entrada']:.2f}`\n"
                    f"Preço atual: `{preco:.2f}`\n"
                    f"Resultado: *{s['resultado']}*"
                )
                enviar_relatorio()

        toque_tol = 0.0005
        reset_dist = 0.03

        # ---------------- SUPORTES ----------------
        for s in SUPORTES:
            n, tf = s["nivel"], s["tf"]
            k = ensure_status(n, tf)
            dist = abs(preco - n) / n

            if dist > reset_dist:
                status[k]["toque"] = False

            if dist <= toque_tol and not status[k]["toque"]:
                classe = classificar_entrada("compra", tf, rsi)
                send_telegram(
                    f"🟢 *SUPORTE {tf}*\n"
                    f"Entrada `{classe}`\n"
                    f"Preço `{preco:.2f}` | RSI `{rsi}`"
                )
                historico.append({
                    "tipo":"compra",
                    "entrada":preco,
                    "nivel":n,
                    "tf":tf,
                    "classe":classe,
                    "hora":datetime.now(),
                    "resultado":"PENDENTE"
                })
                status[k]["toque"] = True

        # ---------------- RESISTÊNCIAS ----------------
        for r in RESISTENCIAS:
            n, tf = r["nivel"], r["tf"]
            k = ensure_status(n, tf)
            dist = abs(preco - n) / n

            if dist > reset_dist:
                status[k]["toque"] = False

            if dist <= toque_tol and not status[k]["toque"]:
                classe = classificar_entrada("venda", tf, rsi)
                send_telegram(
                    f"🔴 *RESISTÊNCIA {tf}*\n"
                    f"Entrada `{classe}`\n"
                    f"Preço `{preco:.2f}` | RSI `{rsi}`"
                )
                historico.append({
                    "tipo":"venda",
                    "entrada":preco,
                    "nivel":n,
                    "tf":tf,
                    "classe":classe,
                    "hora":datetime.now(),
                    "resultado":"PENDENTE"
                })
                status[k]["toque"] = True

        time.sleep(5)

    except Exception as e:
        print("Erro geral:", e, flush=True)
        time.sleep(10)
