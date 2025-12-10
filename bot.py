# ================================
# CONFIGURAÇÕES
# ================================
SUPORTES = [3000, 3050, 3100, 3150, 3200]
RESISTENCIAS = [3300, 3354, 3400, 3500, 3600]

ALERTA_APROXIMACAO = 0.003  # 0.3% de distância
ALERTA_ROMPIMENTO = True     # Ativa alertas de rompimento

rsi_positivo = 35    # RSI abaixo disso = bom para compras
rsi_negativo = 70    # RSI acima disso = bom para vendas

# ================================
# LÓGICA DOS SINAIS
# ================================

def analisar_preco(preco_atual, rsi_atual):
    mensagens = []

    # ====== Verifica Suportes ======
    for suporte in SUPORTES:

        # Aproximação
        if abs(preco_atual - suporte) / suporte <= ALERTA_APROXIMACAO:
            mensagens.append(
                f"🔍 *Aproximação de suporte*: ${preco_atual:.2f} está próximo do suporte ${suporte}. "
                f"(RSI: {rsi_atual})"
            )

        # Teste + Possível Oportunidade
        if preco_atual <= suporte * 1.003 and preco_atual >= suporte * 0.997:
            tipo = "Possível OPORTUNIDADE de COMPRA"  # Mensagem segura
            qualidade = (
                "🟢 *Confluência forte (RSI baixo)*" if rsi_atual <= rsi_positivo 
                else "🟡 *Confluência mediana (RSI neutro)*"
            )
            mensagens.append(
                f"📉 {tipo} no suporte ${suporte}.\nPreço: ${preco_atual:.2f}\nRSI: {rsi_atual} — {qualidade}"
            )

        # Rompimento de suporte
        if ALERTA_ROMPIMENTO and preco_atual < suporte * 0.995:
            mensagens.append(
                f"🚨 *Rompimento de SUPORTE*: preço caiu abaixo de ${suporte}!\n"
                f"Preço atual: ${preco_atual:.2f} | RSI: {rsi_atual}"
            )

    # ====== Verifica Resistências ======
    for resistencia in RESISTENCIAS:

        # Aproximação
        if abs(preco_atual - resistencia) / resistencia <= ALERTA_APROXIMACAO:
            mensagens.append(
                f"🔍 *Aproximação de resistência*: ${preco_atual:.2f} está próximo da resistência ${resistencia}. "
                f"(RSI: {rsi_atual})"
            )

        # Teste + Possível Oportunidade
        if preco_atual >= resistencia * 0.997 and preco_atual <= resistencia * 1.003:
            tipo = "Possível OPORTUNIDADE de VENDA"
            qualidade = (
                "🔴 *Confluência forte (RSI alto)*" if rsi_atual >= rsi_negativo 
                else "🟡 *Confluência mediana (RSI neutro)*"
            )
            mensagens.append(
                f"📈 {tipo} na resistência ${resistencia}.\nPreço: ${preco_atual:.2f}\nRSI: {rsi_atual} — {qualidade}"
            )

        # Rompimento de resistência
        if ALERTA_ROMPIMENTO and preco_atual > resistencia * 1.005:
            mensagens.append(
                f"🚨 *Rompimento de RESISTÊNCIA*: preço passou acima de ${resistencia}!\n"
                f"Preço atual: ${preco_atual:.2f} | RSI: {rsi_atual}"
            )

    return mensagens
