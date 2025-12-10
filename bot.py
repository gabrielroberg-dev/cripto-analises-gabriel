import time
import requests
import math

# -----------------------------
# CONFIG TELEGRAM (já seus)
# -----------------------------
BOT_TOKEN = "8348692375:AAEI_Fcuq5zBd6Il5YPZSj2XtbsXIPLMwyM"
CHAT_ID = "1793725704"

# -----------------------------
# CONFIG GERAL
# -----------------------------
SYMBOL = "ETH"
KRAKEN_PAIR = "ETHUSDT"
CANDLE_INTERVAL = 60             # 1h candles
CANDLES_NEEDED = 200
LOOP_SLEEP = 60                  # <<< MAIS SEGURO E ESTÁVEL

TOUCH_UPPER = 1.003
TOUCH_LOWER = 0.997
ROMPEU_CIMA = 1.005
ROMPEU_BAIXO = 0.995

print("BOT ETH+INDICADORES INICIADO 🚀")


def send_telegram(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print("[ERRO TELEGRAM]", e)


def fetch_ohlc_kraken(pair=KRAKEN_PAIR, interval=CANDLE_INTERVAL):
    try:
        url = "https://api.kraken.com/0/public/OHLC"
        params = {"pair": pair, "interval": interval}
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        if "error" in data and data["error"]:
            print("[Kraken OHLC] Erro:", data["error"])
            return []
        key = list(data["result"].keys())[0]
        ohlc = data["result"][key]
        closes = [float(c[4]) for c in ohlc if len(c) >= 5]
        return closes
    except Exception as e:
        print("[ERR] fetch_ohlc_kraken:", e)
        return []


def ema_from_list(values, period):
    n = len(values)
    if n < period:
        return None
    k = 2 / (period + 1)
    seed = sum(values[:period]) / period
    ema_prev = seed
    for price in values[period:]:
        ema_prev = (price - ema_prev) * k + ema_prev
    return ema_prev


def rsi_from_list(values, period=14):
    n = len(values)
    if n < period + 1:
        return None
    gains = []
    losses = []
    for i in range(1, period + 1):
        delta = values[i] - values[i - 1]
        gains.append(max(delta, 0))
        losses.append(max(-delta, 0))
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    rsi_prev = 100 - (100 / (1 + rs))
    for i in range(period + 1, n):
        delta = values[i] - values[i - 1]
        gain = max(delta, 0)
        loss = max(-delta, 0)
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
        rs = avg_gain / avg_loss if avg_loss != 0 else 999
        rsi_prev = 100 - (100 / (1 + rs))
    return rsi_prev


SUPORTES = [3000, 3238, 2900, 2800, 2700]
RESISTENCIAS = [3300, 3354, 3400, 3500, 3600]

dynamic_supports = set(SUPORTES)
dynamic_resistances = set(RESISTENCIAS)

last_signal = {}


def classify_opportunity(price, suporte, resistencia, rsi_val, ema20, ema50):
    if price <= suporte * TOUCH_UPPER:
        if rsi_val and ema20 and ema50:
            if rsi_val < 35 and ema20 > ema50:
                return "compra", "MUITO BOA"
            if rsi_val < 50:
                return "compra", "MEDIANA"
            return None, None
        return "compra", "MEDIANA"

    if price >= resistencia * TOUCH_LOWER:
        if rsi_val and ema20 and ema50:
            if rsi_val > 65 and ema20 < ema50:
                return "venda", "MUITO BOA"
            if rsi_val > 50:
                return "venda", "MEDIANA"
            return None, None
        return "venda", "MEDIANA"

    return None, None


def detect_sr_from_dynamic(price):
    supports = sorted(dynamic_supports)
    resistances = sorted(dynamic_resistances)
    suporte = max([s for s in supports if s <= price], default=min(supports))
    resistencia = min([r for r in resistances if r >= price], default=max(resistances))
    return suporte, resistencia


while True:
    try:
        closes = fetch_ohlc_kraken()
        if not closes:
            time.sleep(LOOP_SLEEP)
            continue

        ema20 = ema_from_list(closes, 20)
        ema50 = ema_from_list(closes, 50)
        rsi14 = rsi_from_list(closes, 14)

        price = closes[-1]

        suporte, resistencia = detect_sr_from_dynamic(price)

        print("\n=======================================")
        print(f"[ETH] Preço: {price:.2f}")
        print("EMA20:", ema20, "| EMA50:", ema50, "| RSI:", round(rsi14, 2) if rsi14 else "n/a")
        print(f"Suporte: {suporte} | Resistência: {resistencia}")
        print("=======================================\n")

        # FLIP PRA CIMA
        if price > resistencia * ROMPEU_CIMA:
            if resistencia in dynamic_resistances:
                dynamic_resistances.remove(resistencia)
                dynamic_supports.add(resistencia)
            key = f"{resistencia}_rompeu_resistencia"
            if last_signal.get(key) != "sent":
                send_telegram(
                    f"🚀 *Rompimento de Resistência - ETH*\n\n"
                    f"Preço: `{price:.2f}`\n"
                    f"Resistência `{resistencia}` virou *SUPORTE*.\n"
                    f"🔥 Estrutura de alta!"
                )
                last_signal[key] = "sent"

        # FLIP PRA BAIXO
        elif price < suporte * ROMPEU_BAIXO:
            if suporte in dynamic_supports:
                dynamic_supports.remove(suporte)
                dynamic_resistances.add(suporte)
            key = f"{suporte}_rompeu_suporte"
            if last_signal.get(key) != "sent":
                send_telegram(
                    f"⚠️ *Rompimento de Suporte - ETH*\n\n"
                    f"Preço: `{price:.2f}`\n"
                    f"Suporte `{suporte}` virou *RESISTÊNCIA*.\n"
                    f"🚨 Estrutura de baixa!"
                )
                last_signal[key] = "sent"

        else:
            action, quality = classify_opportunity(price, suporte, resistencia, rsi14, ema20, ema50)

            if action:
                key = f"{suporte if action=='compra' else resistencia}_{action}"

                if last_signal.get(key) != "sent":
                    if action == "compra":
                        send_telegram(
                            f"🔵 *Possível Oportunidade de Compra - ETH*\n\n"
                            f"Preço: `{price:.2f}`\n"
                            f"Suporte: `{suporte}`\n"
                            f"Classificação: *{quality}*\n"
                            f"RSI={round(rsi14,2)} | EMA20={round(ema20,2)} | EMA50={round(ema50,2)}\n\n"
                            f"⚠️ Analise antes de operar."
                        )
                    else:
                        send_telegram(
                            f"🔴 *Possível Oportunidade de Venda - ETH*\n\n"
                            f"Preço: `{price:.2f}`\n"
                            f"Resistência: `{resistencia}`\n"
                            f"Classificação: *{quality}*\n"
                            f"RSI={round(rsi14,2)} | EMA20={round(ema20,2)} | EMA50={round(ema50,2)}\n\n"
                            f"⚠️ Analise antes de operar."
                        )

                    last_signal[key] = "sent"

            if suporte < price < resistencia:
                for lvl in list(last_signal.keys()):
                    if lvl.startswith(f"{suporte}_") or lvl.startswith(f"{resistencia}_"):
                        last_signal.pop(lvl, None)

        time.sleep(LOOP_SLEEP)

    except Exception as e:
        print("[ERR MAIN LOOP]", e)
        time.sleep(LOOP_SLEEP)
