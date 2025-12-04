import requests
import time
import pandas as pd
import ta

# ================================
#  CONFIGURAÇÃO TELEGRAM
# ================================
BOT_TOKEN = "8348692375:AAEI_Fcuq5zBd6Il5YPZSj2XtbsXIPLMwyM"
CHAT_ID = 1793725704

def send_telegram(message):
    """Envia mensagem para o Telegram"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.post(url, data=payload, timeout=5)
    except Exception as e:
        print("Erro enviando Telegram:", e)

# ================================
#  ATIVOS E SUPORTE/RESISTÊNCIA
# ================================
ativos = ["BTC", "ETH", "SOL", "NEAR", "WAVE", "SAGA"]

suportes_resistencias = {
    "BTC": {"1h":{"S":[28500,28000],"R":[29500,30000]},
            "4h":{"S":[28000],"R":[30000]},
            "1d":{"S":[27000],"R":[31000]},
            "1w":{"S":[25000],"R":[35000]}},
    "ETH": {"1h":{"S":[1700],"R":[1800]},
            "4h":{"S":[1650],"R":[1850]},
            "1d":{"S":[1600],"R":[1900]},
            "1w":{"S":[1500],"R":[2000]}},
    "SOL": {"1h":{"S":[20],"R":[22]},
            "4h":{"S":[19],"R":[23]},
            "1d":{"S":[18],"R":[25]},
            "1w":{"S":[15],"R":[30]}},
    "NEAR": {"1h":{"S":[2.5],"R":[3.0]},
             "4h":{"S":[2.4],"R":[3.2]},
             "1d":{"S":[2.0],"R":[3.5]},
             "1w":{"S":[1.8],"R":[4.0]}},
    "WAVE": {"1h":{"S":[0.08],"R":[0.1]},
             "4h":{"S":[0.07],"R":[0.12]},
             "1d":{"S":[0.06],"R":[0.15]},
             "1w":{"S":[0.05],"R":[0.2]}},
    "SAGA": {"1h":{"S":[0.3],"R":[0.35]},
             "4h":{"S":[0.28],"R":[0.38]},
             "1d":{"S":[0.25],"R":[0.4]},
             "1w":{"S":[0.2],"R":[0.45]}}
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

    # Detecta rompimento de nível
    sinal = None
    alerta = None
    if trend == "ALTA" and price <= suporte and rsi < 35:
        sinal = "COMPRA ⚡ OPORTUNIDADE CRÍTICA"
        alerta = True
    elif trend == "BAIXA" and price >= resistencia and rsi > 65:
        sinal = "VENDA ⚡ OPORTUNIDADE CRÍTICA"
        alerta = True

    return {
        "price": price,
        "RSI": rsi,
        "MA50": ma50,
        "MA200": ma200,
        "suporte": suporte,
        "resistencia": resistencia,
        "trend": trend,
        "sinal": sinal,
        "alerta": alerta
    }

# ================================
#  LOOP PRINCIPAL VIP (DEBUG)
# ================================
def run_bot():
    print("🚀 Ultimate VIP Bot iniciado!")

    last_signals = {}

    while True:
        for ativo in ativos:
            for tf in ["1h","4h","1d","1w"]:
                print(f"Verificando sinais para {ativo} no timeframe {tf}...")
                result = analyze(ativo, timeframe=tf)
                if result:
                    print(f"Preço atual {ativo}: {result['price']} | Tendência: {result['trend']} | RSI: {round(result['RSI'],2)}")
                if result and result["sinal"] and result["alerta"]:
                    key = f"{ativo}_{tf}"
                    if last_signals.get(key) != result["sinal"]:
                        message = (
                            f"📊 *Sinal Ultimate VIP - {ativo}/USDT*\n"
                            f"⏱ Timeframe: {tf}\n"
                            f"💰 Preço: {result['price']}\n"
                            f"📌 Suporte próximo: {result['suporte']}\n"
                            f"📌 Resistência próxima: {result['resistencia']}\n"
                            f"📈 Tendência: {result['trend']}\n"
                            f"📣 {result['sinal']}\n"
                            f"RSI: {round(result['RSI'],2)} | MA50: {round(result['MA50'],2)} | MA200: {round(result['MA200'],2)}"
                        )
                        send_telegram(message)
                        print("Mensagem enviada para Telegram!")
                        print("="*40)
                        last_signals[key] = result["sinal"]
        print("Aguardando 5 minutos para próxima verificação...\n")
        time.sleep(300)  # Atualiza a cada 5 minutos

if __name__ == "__main__":
    run_bot()
