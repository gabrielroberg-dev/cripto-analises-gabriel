import time
import requests
import hmac
import hashlib
import threading

API_KEY = "SUA_API_KEY_AQUI"
API_SECRET = "SUA_SECRET_AQUI"
BASE_URL = "https://api.mexc.com"

# ========================
# UTILIDADES MEXC
# ========================
def assinatura(params: dict):
    query = "&".join([f"{k}={v}" for k, v in params.items()])
    return hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()

def get_preco(symbol):
    r = requests.get(BASE_URL + "/api/v3/ticker/price", params={"symbol": symbol})
    return float(r.json()["price"])

def order_market(symbol, side, quantidade):
    endpoint = "/api/v3/order"
    params = {
        "symbol": symbol,
        "side": side,
        "type": "MARKET",
        "quantity": quantidade,
        "timestamp": int(time.time()*1000)
    }
    params["signature"] = assinatura(params)
    r = requests.post(BASE_URL + endpoint, headers={"X-MEXC-APIKEY": API_KEY}, params=params)
    print("Ordem enviada:", r.json())
    return r.json()

# ========================
# SUPORTE / RESISTÊNCIA
# ========================
def pegar_candles(symbol, interval="1h", limit=200):
    r = requests.get(BASE_URL + "/api/v3/klines", params={
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    })
    return r.json()

def calcular_sr(candles):
    highs = [float(c[2]) for c in candles]
    lows = [float(c[3]) for c in candles]

    resistencias = sorted(list(set(highs)))[-5:]
    suportes = sorted(list(set(lows)))[:5]

    return suportes, resistencias

# ========================
# LÓGICA DO BOT
# ========================
def analisar(symbol, tf, state):
    candles = pegar_candles(symbol, tf)
    preco = get_preco(symbol)

    suportes, resistencias = calcular_sr(candles)

    # Evitar erro caso listas fiquem vazias
    if not suportes:
        suportes = [preco]
    if not resistencias:
        resistencias = [preco]

    s_prox = max([s for s in suportes if s <= preco], default=suportes[-1])
    r_prox = min([r for r in resistencias if r >= preco], default=resistencias[0])

    print(f"{symbol} | Preço: {preco} | Suporte próximo: {s_prox} | Resistência próxima: {r_prox}")

    # ========================
    # COMPRA AUTOMÁTICA
    # ========================
    if preco <= s_prox and state["pos"] == 0:
        print("🟢 COMPRA EXECUTADA")
        order_market(symbol, "BUY", state["qtd"])
        state["pos"] = 1
        state["entrada"] = preco

    # ========================
    # STOP GAIN
    # ========================
    if state["pos"] == 1 and preco >= state["entrada"] * (1 + state["gain"]):
        print("🟩 STOP GAIN ATIVO")
        order_market(symbol, "SELL", state["qtd"])
        state["pos"] = 0

    # ========================
    # STOP LOSS
    # ========================
    if state["pos"] == 1 and preco <= state["entrada"] * (1 - state["loss"]):
        print("🟥 STOP LOSS ATIVO")
        order_market(symbol, "SELL", state["qtd"])
        state["pos"] = 0


# =========================
# THREADS DO BOT
# =========================
def iniciar(symbol):
    state = {
        "pos": 0,
        "entrada": 0,
        "qtd": 0.003,   # AJUSTE SUA QUANTIDADE
        "gain": 0.003,  # 0.3% STOP GAIN
        "loss": 0.003   # 0.3% STOP LOSS
    }

    while True:
        try:
            analisar(symbol, "1h", state)
        except Exception as e:
            print("Erro:", e)
        
        time.sleep(10)

# =========================
# EXECUÇÃO EM PARALELO
# =========================
threading.Thread(target=iniciar, args=("BTCUSDT",)).start()
threading.Thread(target=iniciar, args=("ETHUSDT",)).start()

print("BOT INICIADO 🚀")
