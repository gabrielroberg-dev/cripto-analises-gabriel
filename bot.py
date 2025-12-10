#!/usr/bin/env python3
"""
BOT ETH - Suportes/Resistências + Aproximação + Rompimento + RSI + MAs + Anti-spam
Pronto para rodar no Render (apenas ETH por enquanto).
"""

import time
import requests
import math
import numpy as np
from typing import List, Optional, Tuple

# =========================
# CONFIGURAÇÃO
# =========================
BOT_TOKEN = "8348692375:AAEI_Fcuq5zBd6Il5YPZSj2XtbsXIPLMwyM"
CHAT_ID = "1793725704"

# Ativo
PAIR = "ETHUSDT"

# Suportes / Resistências (ajuste à vontade)
SUPORTES: List[float] = [3000.0, 3238.0, 2900.0, 2800.0, 2700.0]
RESISTENCIAS: List[float] = [3300.0, 3354.0, 3400.0, 3500.0, 3600.0]

# Parâmetros do bot
LOOP_INTERVAL = 20               # segundos entre iterações (ajuste com cautela)
APPROACH_PCT = 0.003             # 0.3% aproximação (ou usar ABS_MIN)
APPROACH_ABS_MIN = 5.0           # valor absoluto mínimo em USD para aproximação
TOUCH_TOLERANCE_PCT = 0.003      # 0.3% -> considera "tocou"
BREAKOUT_PCT = 0.005             # 0.5% -> considera rompimento
RSI_PERIOD = 14
SMA_SHORT = 20
SMA_LONG = 50

# Cooldowns anti-spam (segundos)
COOLDOWN_APPROACH = 600          # 10 minutos entre alertas de aproximação por zona
COOLDOWN_SIGNAL = 1800           # 30 minutos entre sinais de toque/rompimento por zona

# Timeouts / retries
HTTP_TIMEOUT = 6.0
MAX_RETRIES = 2

# =========================
# HELPERS TELEGRAM / LOG
# =========================
def log(*args, **kwargs):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}]", *args, **kwargs)


def send_telegram(text: str):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
        requests.post(url, data=payload, timeout=HTTP_TIMEOUT)
        log("[TELEGRAM] enviado")
    except Exception as e:
        log("[ERRO TELEGRAM]", e)


# =========================
# PEGAR PREÇO E HISTÓRICO (KRAKEN)
# =========================
def safe_get(url: str, params=None, retries=MAX_RETRIES):
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, params=params, timeout=HTTP_TIMEOUT, headers={"User-Agent": "gabriel-bot/1.0"})
            return r
        except Exception as e:
            log(f"[HTTP] tentativa {attempt} falhou: {e}")
            time.sleep(0.5 * attempt)
    return None


def get_eth_price() -> Optional[float]:
    """
    Usa Kraken (public ticker) para obter preço spot ETHUSDT
    """
    try:
        url = "https://api.kraken.com/0/public/Ticker"
        params = {"pair": PAIR}
        r = safe_get(url, params=params)
        if not r:
            return None
        data = r.json()
        if "error" in data and data["error"]:
            log("[Kraken] erro:", data["error"])
            return None
        key = list(data["result"].keys())[0]
        price = float(data["result"][key]["c"][0])
        return price
    except Exception as e:
        log("[ERRO] get_eth_price:", e)
        return None


def get_eth_history(interval_minutes: int = 60, count: int = 200) -> Optional[List[float]]:
    """
    Puxa candles OHLC do Kraken. interval em minutos (1,5,15,60,240,1440).
    Retorna lista de closes (float), mais recentes por último.
    """
    try:
        url = "https://api.kraken.com/0/public/OHLC"
        params = {"pair": PAIR, "interval": interval_minutes}
        r = safe_get(url, params=params)
        if not r:
            return None
        data = r.json()
        if "error" in data and data["error"]:
            log("[Kraken OHLC] erro:", data["error"])
            return None
        key = list(data["result"].keys())[0]
        candles = data["result"][key]
        closes = [float(c[4]) for c in candles]  # índice 4 = close
        # devolve só os últimos `count`
        return closes[-count:]
    except Exception as e:
        log("[ERRO] get_eth_history:", e)
        return None


# =========================
# INDICADORES (RSI, SMA)
# =========================
def simple_sma(values: List[float], period: int) -> Optional[float]:
    if not values or len(values) < period:
        return None
    return float(np.mean(values[-period:]))


def compute_rsi(closes: List[float], period: int = RSI_PERIOD) -> Optional[float]:
    if not closes or len(closes) < period + 1:
        return None
    deltas = np.diff(np.array(closes))
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    # Wilder's smoothing would be better, mas média simples serve aqui
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:]) + 1e-8
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return float(rsi)


# =========================
# LÓGICA DE S/R E ALERTAS
# =========================
def find_nearest_levels(price: float, supports: List[float], resistances: List[float]) -> Tuple[float, float]:
    supports_sorted = sorted(supports)
    resistances_sorted = sorted(resistances)
    # suporte mais próximo <= price
    s_candidates = [s for s in supports_sorted if s <= price]
    r_candidates = [r for r in resistances_sorted if r >= price]
    s_prox = max(s_candidates) if s_candidates else supports_sorted[0]
    r_prox = min(r_candidates) if r_candidates else resistances_sorted[-1]
    return float(s_prox), float(r_prox)


def is_close(a: float, b: float) -> bool:
    pct = abs(a - b) / b if b != 0 else float("inf")
    abs_diff = abs(a - b)
    return (pct <= APPROACH_PCT) or (abs_diff <= APPROACH_ABS_MIN)


# =========================
# Estado e cooldowns (anti-spam)
# =========================
last_sent = {}  # chave -> timestamp do último envio

def can_send(key: str, cooldown: int) -> bool:
    now = time.time()
    last = last_sent.get(key)
    if last is None or (now - last) >= cooldown:
        last_sent[key] = now
        return True
    return False


# =========================
# MAIN LOOP & lógica
# =========================
def analyze_and_alert():
    # pegar preço e histórico
    price = get_eth_price()
    history = get_eth_history(interval_minutes=60, count=120)  # hourly candles, últimos 120
    if price is None:
        log("Falha ao obter preço.")
        return

    if not history or len(history) < max(RSI_PERIOD + 5, SMA_LONG + 5):
        log("Histórico insuficiente para indicadores. Apenas status.")
        rsi = None
        sma_short = None
        sma_long = None
    else:
        rsi = compute_rsi(history, period=RSI_PERIOD)
        sma_short = simple_sma(history, SMA_SHORT)
        sma_long = simple_sma(history, SMA_LONG)

    s_prox, r_prox = find_nearest_levels(price, SUPORTES, RESISTENCIAS)

    # logs
    log(f"[ETH] Preço: {price:.2f} | Suporte: {s_prox} | Resistência: {r_prox} | RSI: {rsi if rsi else 'n/a'} | MA{SMA_SHORT}:{sma_short if sma_short else 'n/a'} MA{SMA_LONG}:{sma_long if sma_long else 'n/a'}")

    # Dinâmica: se preço está acima de uma resistência, transformar aquela resistência em suporte
    # e vice-versa
    # Usar tolerância pequena para evitar flapping
    # Caso se aplique, movemos zona e informamos com cooldown
    if price > r_prox * (1 + 0.002):  # 0.2% acima da resistência -> considera rompida para cima
        key_swap = f"swap_res2sup_{r_prox}"
        if can_send(key_swap, COOLDOWN_SIGNAL):
            # move r_prox -> suportes
            try:
                RESISTENCIAS.remove(r_prox)
            except ValueError:
                pass
            SUPORTES.append(r_prox)
            log(f"[SWAP] Resistência {r_prox} virou suporte (price {price:.2f}).")
            send_telegram(f"🚀 *Rompimento de resistência confirmada* — {r_prox} virou SUPORTE.\nPreço: `{price:.2f}`\nRSI: `{rsi:.2f}`" if rsi else f"🚀 *Rompimento de resistência confirmada* — {r_prox} virou SUPORTE.\nPreço: `{price:.2f}`")
            # não retornamos aqui; queremos checar proximidade/touch também

    if price < s_prox * (1 - 0.002):  # 0.2% abaixo do suporte -> considera rompido para baixo
        key_swap = f"swap_sup2res_{s_prox}"
        if can_send(key_swap, COOLDOWN_SIGNAL):
            try:
                SUPORTES.remove(s_prox)
            except ValueError:
                pass
            RESISTENCIAS.append(s_prox)
            log(f"[SWAP] Suporte {s_prox} virou resistência (price {price:.2f}).")
            send_telegram(f"⚠️ *Rompimento de suporte confirmado* — {s_prox} virou RESISTÊNCIA.\nPreço: `{price:.2f}`\nRSI: `{rsi:.2f}`" if rsi else f"⚠️ *Rompimento de suporte confirmado* — {s_prox} virou RESISTÊNCIA.\nPreço: `{price:.2f}`")

    # Verificar aproximação
    if is_close(price, s_prox):
        key = f"approach_s_{s_prox}"
        if can_send(key, COOLDOWN_APPROACH):
            txt = (
                f"🟡 *Aproximação do Suporte - ETH*\n\n"
                f"Preço: `{price:.2f}`\n"
                f"Suporte: `{s_prox}`\n"
            )
            if rsi:
                txt += f"RSI: `{rsi:.2f}`\n"
                if rsi < 30:
                    txt += "📉 *RSI em sobrevenda — confluência positiva para compra*\n"
            if sma_short and sma_long:
                trend = "ALTA" if sma_short > sma_long else "BAIXA"
                txt += f"Tendência MAs: `{trend}` (MA{SMA_SHORT} {'>' if sma_short> sma_long else '<'} MA{SMA_LONG})\n"
            send_telegram(txt)
            log("[ALERTA] aproximação suporte enviada")

    if is_close(price, r_prox):
        key = f"approach_r_{r_prox}"
        if can_send(key, COOLDOWN_APPROACH):
            txt = (
                f"🟠 *Aproximação da Resistência - ETH*\n\n"
                f"Preço: `{price:.2f}`\n"
                f"Resistência: `{r_prox}`\n"
            )
            if rsi:
                txt += f"RSI: `{rsi:.2f}`\n"
                if rsi > 70:
                    txt += "📈 *RSI em sobrecompra — confluência positiva para venda*\n"
            if sma_short and sma_long:
                trend = "ALTA" if sma_short > sma_long else "BAIXA"
                txt += f"Tendência MAs: `{trend}`\n"
            send_telegram(txt)
            log("[ALERTA] aproximação resistência enviada")

    # Verificar toque (sinal) - mais estrito (TOUCH_TOLERANCE_PCT)
    if abs(price - s_prox) / s_prox <= TOUCH_TOLERANCE_PCT:
        key = f"signal_touch_s_{s_prox}"
        if can_send(key, COOLDOWN_SIGNAL):
            txt = (
                f"🟢 *Possível oportunidade de COMPRA - ETH*\n\n"
                f"Preço atual: `{price:.2f}`\n"
                f"Suporte tocado: `{s_prox}`\n"
            )
            if rsi:
                txt += f"RSI: `{rsi:.2f}`\n"
            if sma_short and sma_long:
                trend = "ALTA" if sma_short > sma_long else "BAIXA"
                txt += f"Tendência MAs: `{trend}`\n"
            txt += "_Sempre faça sua própria análise antes de operar._"
            send_telegram(txt)
            log("[SINAL] toque suporte enviado")

    if abs(price - r_prox) / r_prox <= TOUCH_TOLERANCE_PCT:
        key = f"signal_touch_r_{r_prox}"
        if can_send(key, COOLDOWN_SIGNAL):
            txt = (
                f"🔴 *Possível oportunidade de VENDA - ETH*\n\n"
                f"Preço atual: `{price:.2f}`\n"
                f"Resistência tocada: `{r_prox}`\n"
            )
            if rsi:
                txt += f"RSI: `{rsi:.2f}`\n"
            if sma_short and sma_long:
                trend = "ALTA" if sma_short > sma_long else "BAIXA"
                txt += f"Tendência MAs: `{trend}`\n"
            txt += "_Sempre faça sua própria análise antes de operar._"
            send_telegram(txt)
            log("[SINAL] toque resistência enviado")

    # Rompimento (breakout) - maior distância
    if price > r_prox * (1 + BREAKOUT_PCT):
        key = f"breakout_r_{r_prox}"
        if can_send(key, COOLDOWN_SIGNAL):
            txt = (
                f"🚀 *Rompimento de Resistência - ETH*\n\n"
                f"Resistência: `{r_prox}`\n"
                f"Preço atual: `{price:.2f}`\n"
            )
            if rsi:
                txt += f"RSI: `{rsi:.2f}`\n"
            send_telegram(txt)
            log("[BREAKOUT] resistência")

    if price < s_prox * (1 - BREAKOUT_PCT):
        key = f"breakout_s_{s_prox}"
        if can_send(key, COOLDOWN_SIGNAL):
            txt = (
                f"⚠️ *Rompimento de Suporte - ETH*\n\n"
                f"Suporte: `{s_prox}`\n"
                f"Preço atual: `{price:.2f}`\n"
            )
            if rsi:
                txt += f"RSI: `{rsi:.2f}`\n"
            send_telegram(txt)
            log("[BREAKOUT] suporte")


# =========================
# START
# =========================
def main():
    log("BOT ETH INICIADO 🚀 (apenas ETH)")
    # Normalize lists as floats (defensivo)
    global SUPORTES, RESISTENCIAS
    SUPORTES = [float(x) for x in SUPORTES]
    RESISTENCIAS = [float(x) for x in RESISTENCIAS]

    # Loop principal
    while True:
        try:
            analyze_and_alert()
        except Exception as e:
            log("[EXCEPTION no loop principal]", e)
        time.sleep(LOOP_INTERVAL)


if __name__ == "__main__":
    main()
