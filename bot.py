import requests
import time
import pandas as pd
import ta
import threading

# ================================
#  CONFIGURAÇÃO TELEGRAM
# ================================
BOT_TOKEN = "8348692375:AAEI_Fcuq5zBd6Il5YPZSj2XtbsXIPLMwyM"
CHAT_ID = 1793725704

DEBUG = True  # True para logs detalhados

def send_telegram(message):
    """Envia mensagem para o Telegram"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.post(url, data=payload, timeout=5)
    except Exception as e:
        if DEBUG:
            print("Erro enviando Telegram:", e)

# ================================
#  ATIVOS E SUPORTE/RESISTÊNCIA
# ================================
ativos = ["BTC", "ETH"]

suportes_resistencias = {
    "BTC": {"1h":{"S":[28500,28000],"R":[29500,30000]},
            "4h":{"S":[28000],"R":[30000]},
            "1d":{"S":[27000],"R":[31000]},
            "1w":{"S":[25000],"R":[35000]},
            "1m":{"S":[24000],"R":[36000]}},
    "ETH": {
        "4h": {"S":[2970.75], "R":[3833.01]},
        "1d": {"S":[3038.98, 2526.17, 2526.17], "R":[3237.49, 3353.29, 4213.49]},
        "1w": {"S":[2902.47, 2372.62], "R":[4368.80, 35000]},
        "1m": {"S":[2729.05, 2144.50, 0.0], "R":[4057.49, 3472.96, 4774.86]}
    }
}

# ================================
#  PEGAR HISTÓRICO DE PREÇO
# ================================
def get_ohlcv(symbol, days=7):
    coin_id = symbol.lower()
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/ohlc?vs_currency=usd&days={days}"
        r = requests.get(url, timeout=5)
        data = r.json()
        df = pd.DataFrame(data, columns=["timestamp","open","high","low","close"])
        df["close"] = df["close"].astype(float)
        return df
    except Exception as e:
        if DEBUG:
            print(f"Erro OHLCV {symbol}:", e)
        return pd.DataFrame()

# ================================
#  ANÁLISE TÉCNICA VIP
# ================================
def analyze(symbol, timeframe="1h"):
    df = get_ohlcv(symbol)
    if df.empty:
        return None

    close = df["close"]
    price = close.iloc[-1]

    # Médias móveis
    ma50 = close.rolling(window=50).mean().iloc[-1]
    ma200 = close.rolling(window=200).mean().iloc[-1]

    # RSI
    rsi = ta.momentum.RSIIndicator(close, window=14).rsi().iloc[-1]

    # Tendência
    trend = "ALTA" if ma50 > ma200 else "BAIXA"

    # Suporte e resistência próximos
    nivel = suportes_resistencias[symbol][timeframe]
    suporte = min([s for s in nivel["S"] if s <= price] + [nivel["S"][0]])
    resistencia = min([r for r in nivel["R"] if r >= price] + [nivel["R"][0]])

    # Mini gráfico ASCII
    grafico = ""
    for s in nivel["S"]:
        grafico += f"S{s} "
    for r in nivel["R"]:
        grafico += f"R{r} "
    grafico += f"P{price}"

    # Detecta rompimento e atualiza níveis
    sinal = None
    alerta = None
    if trend == "ALTA" and price <= suporte and rsi < 35:
        sinal = "COMPRA ⚡ OPORTUNIDADE CRÍTICA"
        alerta = True
    elif trend == "BAIXA" and price >= resistencia and rsi > 65:
        sinal = "VENDA ⚡ OPORTUNIDADE CRÍTICA"
        alerta = True

    # Rompimento -> inverter níveis
    if price > resistencia:
        nivel["S"].append(resistencia)
        nivel["R"].remove(resistencia)
        if DEBUG: print(f"[INFO] {symbol} {timeframe}: Resistência {resistencia} rompida, virou suporte!")
    if price < suporte:
        nivel["R"].append(suporte)
        nivel["S"].remove(suporte)
        if DEBUG: print(f"[INFO] {symbol} {timeframe}: Suporte {suporte} rompido, virou resistência!")

    return {
        "price": price,
        "RSI": rsi,
        "MA50": ma50,
        "MA200": ma200,
        "suporte": suporte,
        "resistencia": resistencia,
        "trend": trend,
        "sinal": sinal,
        "alerta": alerta,
        "grafico": grafico
    }

# ================================
#  FUNÇÃO DE THREAD PARA CADA ATIVO/TIMEFRAME
# ================================
def run_ativo(ativo, timeframe, last_signals):
    while True:
        result = analyze(ativo, timeframe)
        if result and result["sinal"] and result["alerta"]:
            key = f"{ativo}_{timeframe}"
            if last_signals.get(key) != result["sinal"]:
                message = (
                    f"📊 *Sinal Ultimate VIP - {ativo}/USDT*\n"
                    f"⏱ Timeframe: {timeframe}\n"
                    f"💰 Preço: {result['price']}\n"
                    f"📌 Suporte próximo: {result['suporte']}\n"
                    f"📌 Resistência próxima: {result['resistencia']}\n"
                    f"📈 Tendência: {result['trend']}\n"
                    f"📣 {result['sinal']}\n"
                    f"RSI: {round(result['RSI'],2)} | MA50: {round(result['MA50'],2)} | MA200: {round(result['MA200'],2)}\n"
                    f"🖥 Mini gráfico: {result['grafico']}"
                )
                send_telegram(message)
                if DEBUG:
                    print(f"[ALERTA] {ativo} {timeframe}: {result['sinal']} enviado ao Telegram!")
                last_signals[key] = result["sinal"]
        elif DEBUG:
            print(f"[INFO] {ativo} {timeframe}: sem sinal crítico.")
        time.sleep(300)  # Atualiza a cada 5 minutos

# ================================
#  LOOP PRINCIPAL VIP
# ================================
def run_bot():
    print("🚀 Ultimate VIP Bot iniciado!")
    last_signals = {}

    threads = []
    for ativo in ativos:
        for tf in ["1h","4h","1d","1w","1m"]:
            t = threading.Thread(target=run_ativo, args=(ativo, tf, last_signals))
            t.daemon = True
            t.start()
            threads.append(t)

    # Heartbeat principal
    while True:
        if DEBUG:
            print(f"[{time.strftime('%H:%M:%S')}] Bot rodando com threads ativas...")
        time.sleep(300)

if __name__ == "__main__":
    run_bot()
