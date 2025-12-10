# flags por nível
alertas_enviados = {
    "rompeu_suporte": set(),
    "rompeu_resistencia": set(),
    "toque_suporte": set(),
    "toque_resistencia": set(),
    "aprox_suporte": set(),
    "aprox_resistencia": set()
}

while True:
    preco = get_eth_price()
    if not preco:
        time.sleep(5)
        continue

    suporte, resistencia = detectar_sr(preco)

    # distância segura para reset
    distancia_reset = 0.02  # 2%

    # =============================
    # RESET GLOBAL DE ALERTAS POR NÍVEL
    # =============================
    for nivel in list(alertas_enviados["toque_suporte"]):
        if abs(preco - nivel) > nivel * distancia_reset:
            alertas_enviados["toque_suporte"].remove(nivel)

    for nivel in list(alertas_enviados["toque_resistencia"]):
        if abs(preco - nivel) > nivel * distancia_reset:
            alertas_enviados["toque_resistencia"].remove(nivel)

    for nivel in list(alertas_enviados["rompeu_suporte"]):
        if abs(preco - nivel) > nivel * distancia_reset:
            alertas_enviados["rompeu_suporte"].remove(nivel)

    for nivel in list(alertas_enviados["rompeu_resistencia"]):
        if abs(preco - nivel) > nivel * distancia_reset:
            alertas_enviados["rompeu_resistencia"].remove(nivel)

    for nivel in list(alertas_enviados["aprox_suporte"]):
        if abs(preco - nivel) > nivel * distancia_reset:
            alertas_enviados["aprox_suporte"].remove(nivel)

    for nivel in list(alertas_enviados["aprox_resistencia"]):
        if abs(preco - nivel) > nivel * distancia_reset:
            alertas_enviados["aprox_resistencia"].remove(nivel)

    # =============================
    # ROMPEU RESISTÊNCIA
    # =============================
    if preco > resistencia * 1.005:
        if resistencia not in alertas_enviados["rompeu_resistencia"]:
            send_telegram(
                f"🚀 Rompimento da RESISTÊNCIA - ETH\n"
                f"Preço: {preco:.2f}\nNível: {resistencia}"
            )
            alertas_enviados["rompeu_resistencia"].add(resistencia)

            dynamic_resistances.discard(resistencia)
            dynamic_supports.add(resistencia)

    # =============================
    # ROMPEU SUPORTE
    # =============================
    if preco < suporte * 0.995:
        if suporte not in alertas_enviados["rompeu_suporte"]:
            send_telegram(
                f"⚠️ Rompimento do SUPORTE - ETH\n"
                f"Preço: {preco:.2f}\nNível: {suporte}"
            )
            alertas_enviados["rompeu_suporte"].add(suporte)

            dynamic_supports.discard(suporte)
            dynamic_resistances.add(suporte)

    # =============================
    # TOQUE SUPORTE
    # =============================
    if preco <= suporte * 1.003:
        if suporte not in alertas_enviados["toque_suporte"]:
            send_telegram(
                f"🟢 Toque no SUPORTE - ETH\n"
                f"Preço: {preco:.2f}\nNível: {suporte}"
            )
            alertas_enviados["toque_suporte"].add(suporte)

    # =============================
    # TOQUE RESISTÊNCIA
    # =============================
    if preco >= resistencia * 0.997:
        if resistencia not in alertas_enviados["toque_resistencia"]:
            send_telegram(
                f"🔴 Toque na RESISTÊNCIA - ETH\n"
                f"Preço: {preco:.2f}\nNível: {resistencia}"
            )
            alertas_enviados["toque_resistencia"].add(resistencia)

    # =============================
    # APROX SUPORTE
    # =============================
    if abs(preco - suporte) <= suporte * 0.01:
        if suporte not in alertas_enviados["aprox_suporte"]:
            send_telegram(
                f"🟡 Aproximação do SUPORTE - ETH\n"
                f"Preço: {preco:.2f}\nNível: {suporte}"
            )
            alertas_enviados["aprox_suporte"].add(suporte)

    # =============================
    # APROX RESISTÊNCIA
    # =============================
    if abs(preco - resistencia) <= resistencia * 0.01:
        if resistencia not in alertas_enviados["aprox_resistencia"]:
            send_telegram(
                f"🟠 Aproximação da RESISTÊNCIA - ETH\n"
                f"Preço: {preco:.2f}\nNível: {resistencia}"
            )
            alertas_enviados["aprox_resistencia"].add(resistencia)

    time.sleep(4)
