import time
import requests
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

print("ASSISTENTE CRIPTO ETH (KRAKEN + NEWS) INICIADO 🤖🚀", flush=True)

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
            data={
                "chat_id": CHAT_ID,
                "text": msg,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            },
            timeout=10
        )
    except Exception as e:
        print("Erro Telegram:", e, flush=True)

# =====================================================
# PREÇO ETH – KRAKEN
# =====================================================
def get_eth_price():
    try:
        r = requests.get(
            "https://api.kraken.com/0/public/Ticker?pair=ETHUSD",
            timeout=10
        ).json()
        pair = list(r["result"].keys())[0]
        return float(r["result"][pair]["c"][0])
    except Exception as e:
        print("Erro preço:", e, flush=True)
        return None

# =====================================================
# RSI 5m – KRAKEN
# =====================================================
def get_rsi(period=14):
    try:
        r = requests.get(
            "https://api.kraken.com/0/public/OHLC?pair=ETHUSD&interval=5",
            timeout=10
        ).json()
        pair = list(r["result"].keys())[0]
        candles = r["result"][pair]
        closes = [float(c[4]) for c in candles][-100:]

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
def classificar_entrada(direcao, tf, rsi):
    score = {"1W":4,"1D":3,"4H":2,"1H":1}.get(tf,0)
    if direcao == "compra":
        score += 3 if rsi <= 30 else 1 if rsi <= 40 else 0
    else:
        score += 3 if rsi >= 70 else 1 if rsi >= 60 else 0
    if score >= 7: return "A+"
    if score >= 4: return "B"
    return "C"

# =====================================================
# ZONAS TÉCNICAS (FLIP AUTOMÁTICO)
# =====================================================
ZONAS = [
    {"nivel": 2800, "tf": "1W"},
    {"nivel": 3000, "tf": "1D"},
    {"nivel": 3128, "tf": "1D"},
    {"nivel": 3238, "tf": "4H"},
    {"nivel": 3300, "tf": "4H"},
    {"nivel": 3500, "tf": "1W"},
]

status = {}

def key(n, tf):
    return f"{n}_{tf}"

def ensure_status(n, tf):
    if key(n, tf) not in status:
        status[key(n, tf)] = {"toque": False}
    return key(n, tf)

# =====================================================
# RSS ETH – NOTÍCIAS (LEVE E SEGURO)
# =====================================================
RSS_FEEDS = [
    "https://www.coindesk.com/arc/outboundfeeds/rss/?tags=ethereum",
    "https://cointelegraph.com/rss/tag/ethereum"
]

PALAVRAS_CHAVE = [
    "ethereum", "eth", "etf", "staking", "upgrade",
    "sec", "layer", "gas", "network"
]

ultima_noticia = datetime.now() - timedelta(minutes=30)
titulos_enviados = set()

def checar_noticias():
    global ultima_noticia

    if datetime.now() - ultima_noticia < timedelta(minutes=15):
        return

    for feed in RSS_FEEDS:
        try:
            r = requests.get(feed, timeout=10)
            root = ET.fromstring(r.content)

            for item in root.findall(".//item")[:3]:
                titulo = item.find("title").text
                link = item.find("link").text

                if titulo in titulos_enviados:
                    continue

                titulo_lower = titulo.lower()
                if not any(p in titulo_lower for p in PALAVRAS_CHAVE):
                    continue

                send_telegram(
                    f"📰 *ETH | NOTÍCIA IMPORTANTE*\n\n"
                    f"{titulo}\n\n"
                    f"[Ler matéria]({link})\n\n"
                    f"_⚠️ Informação educacional. Não é recomendação._"
                )

                titulos_enviados.add(titulo)
                ultima_noticia = datetime.now()
                break

        except Exception as e:
            print("Erro RSS:", e, flush=True)

# =====================================================
# LOOP PRINCIPAL
# =====================================================
send_telegram(
    "🤖 *Assistente Cripto ETH ativo*\n"
    "Análise técnica + notícias\n"
    "Fonte: *Kraken*"
)

while True:
    try:
        preco = get_eth_price()
        rsi = get_rsi()

        if not preco or not rsi:
            time.sleep(15)
            continue

        toque_tol = 0.0005
        reset_dist = 0.03

        for z in ZONAS:
            n, tf = z["nivel"], z["tf"]
            k = ensure_status(n, tf)

            dist = abs(preco - n) / n

            if dist > reset_dist:
                status[k]["toque"] = False

            if dist <= toque_tol and not status[k]["toque"]:

                if preco > n:
                    tipo = "SUPORTE"
                    direcao = "compra"
                    emoji = "🟢"
                else:
                    tipo = "RESISTÊNCIA"
                    direcao = "venda"
                    emoji = "🔴"

                classe = classificar_entrada(direcao, tf, rsi)

                send_telegram(
                    f"{emoji} *ETH | {tipo} ({tf})*\n\n"
                    f"Preço: `{preco:.2f}`\n"
                    f"Nível: `{n}`\n"
                    f"RSI: `{rsi}`\n"
                    f"Força: `{classe}`\n\n"
                    f"_⚠️ Alerta técnico. Não é recomendação._"
                )

                status[k]["toque"] = True

        # 📰 Notícias (controle de tempo)
        checar_noticias()

        time.sleep(15)

    except Exception as e:
        print("Erro geral:", e, flush=True)
        time.sleep(15)
