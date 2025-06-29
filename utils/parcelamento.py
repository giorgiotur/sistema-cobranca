from datetime import datetime, timedelta

def calcular_parcelamento(data_viagem, valor_total: float):
    hoje = datetime.today().date()
    dias_restantes = (data_viagem - hoje).days

    parcelas = []
    mensagem = ""
    parcelamento = 0

    # ✅ NOVA REGRA: Pagamento à vista para viagens com 45 dias ou menos
    if dias_restantes <= 45:
        parcelamento = 1
        parcelas.append({
            "parcela": 1,
            "valor": round(valor_total, 2),
            "vencimento": hoje.strftime("%d/%m/%Y")
        })
        mensagem = "Pagamento à vista - Prazo de vencimento: Hoje. Sugestão: PIX ou Transferência bancária."
        return {"parcelamento": parcelamento, "parcelas": parcelas, "mensagem": mensagem}

    # Condição 46 a 50 dias → 1x
    if 46 <= dias_restantes <= 50:
        parcelamento = 1
        vencimento = hoje + timedelta(days=15)
        parcelas.append({
            "parcela": 1,
            "valor": round(valor_total, 2),
            "vencimento": vencimento.strftime("%d/%m/%Y")
        })
        mensagem = "Parcelamento em 1x com vencimento em 15 dias."

    # Condição 51 a 62 dias → 2x
    elif 51 <= dias_restantes <= 62:
        parcelamento = 2
        valor_parcela = round(valor_total / 2, 2)

        primeira = hoje + timedelta(days=30)
        segunda = data_viagem - timedelta(days=3)

        parcelas.append({"parcela": 1, "valor": valor_parcela, "vencimento": primeira.strftime("%d/%m/%Y")})
        parcelas.append({"parcela": 2, "valor": valor_parcela, "vencimento": segunda.strftime("%d/%m/%Y")})

        mensagem = "Parcelamento em 2x: 1ª em 30 dias, 2ª até 3 dias antes da viagem."

    # Condição acima de 365 dias → Máximo 12x fixas
    elif dias_restantes > 365:
        parcelamento = 12
        valor_parcela = round(valor_total / parcelamento, 2)

        for i in range(1, parcelamento + 1):
            vencimento = hoje + timedelta(days=30 * i)
            if vencimento >= data_viagem:
                vencimento = data_viagem - timedelta(days=3)
            parcelas.append({
                "parcela": i,
                "valor": valor_parcela,
                "vencimento": vencimento.strftime("%d/%m/%Y")
            })

        mensagem = "Parcelamento máximo de 12x."

    # Condição de 63 até 365 dias → Meses completos + ajuste por dias extras
    else:
        meses_completos = dias_restantes // 30
        dias_extras = dias_restantes % 30

        parcelamento = meses_completos
        if dias_extras > 20:
            parcelamento += 1

        if parcelamento > 12:
            parcelamento = 12

        valor_parcela = round(valor_total / parcelamento, 2)

        for i in range(1, parcelamento + 1):
            vencimento = hoje + timedelta(days=30 * i)
            if vencimento >= data_viagem:
                vencimento = data_viagem - timedelta(days=3)
            parcelas.append({
                "parcela": i,
                "valor": valor_parcela,
                "vencimento": vencimento.strftime("%d/%m/%Y")
            })

        mensagem = f"Parcelamento em {parcelamento}x baseado nos meses até a viagem."

    return {
        "parcelamento": parcelamento,
        "parcelas": parcelas,
        "mensagem": mensagem
    }
