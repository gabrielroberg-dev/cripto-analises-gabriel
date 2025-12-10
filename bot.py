ultimo_alerta = {
    "aprox_suporte": False,
    "aprox_resistencia": False,
    "toque_suporte": False,
    "toque_resistencia": False,
    "rompeu_suporte": False,
    "rompeu_resistencia": False
}

while True:
    preco = get_eth_price()
    rsi = get_rsi()

    if not preco or not rsi:
        time.sleep(5)
        continue

    suporte, resistencia = detectar_sr(preco)

    # =============================
    # APROXIMAÇÃO SUPORTE
    # =============================
    if abs(preco - suporte) <= suporte * 0.01:
        if not ultimo_alerta["aprox_suporte"]:
            send_telegram(
                f"🟡 Aproximação do SUPORTE - ETH\n"
                f"Preço: {preco:.2f}\nSuporte: {suporte}\nRSI: {rsi}"
            )
            ultimo_alerta["aprox_suporte"] = True
    else:
        ultimo_alerta["aprox_suporte"] = False

    # =============================
    # APROXIMAÇÃO RESISTÊNCIA
    # =============================
    if abs(preco - resistencia) <= resistencia * 0.01:
        if not ultimo_alerta["aprox_resistencia"]:
            send_telegram(
                f"🟠 Aproximação da RESISTÊNCIA - ETH\n"
                f"Preço: {preco:.2f}\nResistência: {resistencia}\nRSI: {rsi}"
            )
            ultimo_alerta["aprox_resistencia"] = True
    else:
        ultimo_alerta["aprox_resistencia"] = False

    # =============================
    # ROMPIMENTO DE RESISTÊNCIA
    # =============================
    if preco > resistencia * 1.005:
        if not ultimo_alerta["rompeu_resistencia"]:
            send_telegram(
                f"🚀 Rompeu RESISTÊNCIA!\n"
                f"Preço: {preco:.2f}\nVirou suporte: {resistencia}\nRSI: {rsi}"
            )
            ultimo_alerta["rompeu_resistencia"] = True

            if resistencia in dynamic_resistances:
                dynamic_resistances.remove(resistencia)
                dynamic_supports.add(resistencia)

    else:
        ultimo_alerta["rompeu_resistencia"] = False

    # =============================
    # ROMPIMENTO DE SUPORTE
    # =============================
    if preco < suporte * 0.995:
        if not ultimo_alerta["rompeu_suporte"]:
            send_telegram(
                f"⚠️ Rompeu SUPORTE!\n"
                f"Preço: {preco:.2f}\nVirou resistência: {suporte}\nRSI: {rsi}"
            )
            ultimo_alerta["rompeu_suporte"] = True

            if suporte in dynamic_supports:
                dynamic_supports.remove(suporte)
                dynamic_resistances.add(suporte)

    else:
        ultimo_alerta["rompeu_suporte"] = False

    # =============================
    # TOQUE NO SUPORTE
    # =============================
    if preco <= suporte * 1.003:
        if not ultimo_alerta["toque_suporte"]:
            send_telegram(
                f"🟢 TOQUE NO SUPORTE\n"
                f"Preço: {preco:.2f}\nSuporte: {suporte}\nRSI: {rsi}"
            )
            ultimo_alerta["toque_suporte"] = True
    else:
        ultimo_alerta["toque_suporte"] = False

    # =============================
    # TOQUE NA RESISTÊNCIA
    # =============================
    if preco >= resistencia * 0.997:
        if not ultimo_alerta["toque_resistencia"]:
            send_telegram(
                f"🔴 TOQUE NA RESISTÊNCIA\n"
                f"Preço: {preco:.2f}\nResistência: {resistencia}\nRSI: {rsi}"
            )
            ultimo_alerta["toque_resistencia"] = True
    else:
        ultimo_alerta["toque_resistencia"] = False

    time.sleep(5)
