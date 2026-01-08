import time
import requests
from datetime import datetime
import feedparser

# ==============================
# CONFIG
# ==============================
BOT_TOKEN = "SEU_TOKEN"
CHAT_ID = "SEU_CHAT_ID"

KRAKEN_URL = "https://api.kraken.com/0/public/Ticker?pair=ETHUSD"
RSS_URL = "https://cointelegraph.com/rss/tag/ethereum"

INTERVALO_PRECO = 300      # 5 min
INTERVALO_NEWS = 1800      # 30 min

ultimo_preco_msg = 0
ultimo_news_time = None

# ==============================
# TELEGRAM
# ==============================
def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": msg,
            "parse_mode": "HTML"
        }
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print("Erro Telegram:", e)

# ==============================
# PREÇO ETH (KRAKEN)
# ==============================
def get_eth_price():
    try:
        r = requests.get(KRAKEN_URL, timeout=10).json()
        price = float(list(r["result"].values())[0]["c"][0])
        return price
    except Exception as e:
        print("Erro preço:", e)
        return None

# ==============================
# RSS NEWS ETH
# ==============================
def check_news():
    global ultimo_news_time
    try:
        feed = feedparser.parse(RSS_URL)
        if not feed.entries:
            return

        entry = feed.entries[0]
        published = datetime(*entry.published_parsed[:6])

        if ultimo_news_time is None or published > ultimo_news_time:
            ultimo_news_time = published
            msg = (
                "📰 <b>NOTÍCIA ETH</b>\n\n"
                f"🗞 <b>{entry.title}</b>\n\n"
                f"🔗 {entry.link}\n\n"
                "⚠️ Conteúdo informativo, não recomendação."
            )
            send_telegram(msg)

    except Exception as e:
        print("Erro news:", e)

# ==============================
# LOOP PRINCIPAL
# ==============================
print("ASSISTENTE CRIPTO ETH (KRAKEN + NEWS) INICIADO 🤖🚀")

while True:
    agora = time.time()

    # -------- PREÇO --------
    if agora - ultimo_preco_msg > INTERVALO_PRECO:
        price = get_eth_price()
        if price:
            zona = 3238
            if price > zona:
                contexto = "🟢 SUPORTE"
            else:
                contexto = "🔴 RESISTÊNCIA"

            msg = (
                "📊 <b>ETH / USD</b>\n\n"
                f"💰 Preço atual: <b>${price:.2f}</b>\n"
                f"📍 Zona 3238: <b>{contexto}</b>\n\n"
                "🧠 Leitura estrutural de mercado"
            )
            send_telegram(msg)
            ultimo_preco_msg = agora

    # -------- NEWS --------
    check_news()

    time.sleep(20)
