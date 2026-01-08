import time
import requests
import feedparser
from datetime import datetime

print("ASSISTENTE CRIPTO ETH (KRAKEN + NEWS) INICIADO 🤖🚀", flush=True)

# ================== CONFIG TELEGRAM ==================
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

# ================== PREÇO ETH (KRAKEN) ==================
def get_eth_price():
    try:
        r = requests.get(
            "https://api.kraken.com/0/public/Ticker?pair=ETHUSDT",
            timeout=10
        ).json()
        pair = list(r["result"].keys())[0]
        return float(r["result"][pair]["c"][0])
    except Exception as e:
        print("Erro preço:", e, flush=True)
        return None

# ================== RSI ==================
def get_rsi(period=14):
    try:
        r = requests.get(
            "https://api.kraken.com/0/public/OHLC?pair=ETHUSDT&interval=5",
            timeout=10
        ).json()
        pair = list(r["result"].keys())[0]
        closes = [float(c[4]) for c in r["result"][pair]][-100:]

        gains, losses = [], []
        for i in range(1, len(closes)):
            diff = closes[i] - closes[i - 1]
            gains.append(max(diff, 0))
            losses.append(abs(min(diff, 0)))

        avg_gain = sum(gains[-period:]) / period or 0.0001
        avg_loss = sum(losses[-period:]) / period or 0.0001

        rs = avg_gain / avg_loss
        return round(100 - (100 / (1 + rs)), 2)
    except Exception as e:
        print("Erro RSI:", e, flush=True)
        return None

# ================== NÍVEIS ==================
NIVEIS = [
    {"nivel": 3238, "tf": "4H"},
    {"nivel": 3000, "tf": "1D"},
    {"nivel": 3500, "tf": "1W"},
]

status = {}

# ================== NEWS ETH (RSS) ==================
RSS_FEEDS = [
    "https://cointelegraph.com/rss/tag/ethereum",
    "https://cryptonews.com/news/ethereum/feed/"
]

ultimas_news = set()

def check_news():
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:2]:
            if entry.link not in ultimas_news:
                ultimas_news.add(entry.link)
                send_telegram(
                    f"📰 *Notícia ETH*\n\n"
                    f"*{entry.title}*\n"
                    f"{entry.link}"
                )

# ================== LOOP PRINCIPAL ==================
while True:
    try:
        preco = get_eth_price()
        rsi = get_rsi()

        if not preco or not rsi:
            time.sleep(30)
            continue

        for n in NIVEIS:
            nivel = n["nivel"]
            tf = n["tf"]
            key = f"{nivel}_{tf}"

            if key not in status:
                status[key] = False

            dist = abs(preco - nivel) / nivel

            if dist > 0.02:
                status[key] = False

            if dist <= 0.001 and not status[key]:
                tipo = "SUPORTE" if preco > nivel else "RESISTÊNCIA"
                send_telegram(
                    f"{'🟢' if tipo=='SUPORTE' else '🔴'} *{tipo} {tf}*\n\n"
                    f"Preço: `{preco:.2f}`\n"
                    f"Nível: `{nivel}`\n"
                    f"RSI: `{rsi}`\n\n"
                    f"_Não é recomendação de investimento_"
                )
                status[key] = True

        check_news()
        time.sleep(300)

    except Exception as e:
        print("Erro geral:", e, flush=True)
        time.sleep(30)
