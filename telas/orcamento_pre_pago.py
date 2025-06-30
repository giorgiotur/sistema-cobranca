import requests
from datetime import datetime, timedelta
from utils.parcelamento import calcular_parcelamento
import streamlit as st
from dotenv import load_dotenv
from utils.navigation import ir_para
import os

load_dotenv()
URL_API_BACKEND = os.getenv("API_BASE")

def tela_orcamento_pre_pago():
    # 🔷 TEXTO EXPLICATIVO INICIAL
    st.markdown("""
        <div style='background-color:#e8f4ff; padding:15px; border-radius:10px; margin-bottom:20px;'>
            <span style='font-size:36px; font-weight:bold;'>📋 Orçamento Pré-Pago</span><br><br>
            Preencha os dados abaixo para criar um orçamento detalhado da hospedagem.<br>
            <span style='font-size:16px;'>
                Após calcular o parcelamento, você poderá salvar e gerar o documento com todas as informações formatadas.
            </span>
        </div>
    """, unsafe_allow_html=True)


    # -------------------------------
    # BLOCO 1 - DADOS DO PACOTE
    # -------------------------------
    st.markdown("<hr style='border:1px solid #ccc;'>", unsafe_allow_html=True)

    # Fundo visual leve
    st.markdown("""
        <div style='background-color:#f0f0f0; padding:8px; border-radius:5px; margin-bottom:5px;'>
        </div>
    """, unsafe_allow_html=True)

    st.header("📌 Dados do Pacote")
    st.caption("Informe os dados gerais do pacote, incluindo o destino, as datas da viagem, quantidade de noites e o número de pessoas que farão parte da reserva.")

    # Tipo de Pacote
    tipo_pacote = st.selectbox(
        "Tipo de Pacote:",
        ["Selecione...", "Hospedagem Bonito", "Hospedagem Brasil", "Pacote Bonito (Hospedagem + Passeios)"],
        index=st.session_state.get("tipo_pacote_index", 0)
    )
    st.session_state["tipo_pacote_index"] = ["Selecione...", "Hospedagem Bonito", "Hospedagem Brasil", "Pacote Bonito (Hospedagem + Passeios)"].index(tipo_pacote)

    # Destino
    destino = st.selectbox(
        "Destino:",
        ["Bonito", "Nordeste", "Outros"],
        index=st.session_state.get("destino_index", 0)
    )
    st.session_state["destino_index"] = ["Bonito", "Nordeste", "Outros"].index(destino)

    # Data de Ida
    data_ida = st.date_input(
        "Data de Ida (Check-in):",
        value=st.session_state.get("data_ida", datetime.today())
    )
    st.session_state["data_ida"] = data_ida

    # Garantir que o numero_noites nunca seja menor que 1
    numero_noites = st.session_state.get("numero_noites", 1)
    if numero_noites < 1:
        numero_noites = 1
        st.session_state["numero_noites"] = 1

    numero_noites = st.number_input(
        "Número de Noites:",
        min_value=1,
        step=1,
        value=numero_noites,
        key="numero_noites_input"
    )
    st.session_state["numero_noites"] = numero_noites

    # ------------------------------------------
    # Controle de atualização da Data de Volta (Check-out)
    # ------------------------------------------
    if "atualizando_volta" not in st.session_state:
        st.session_state["atualizando_volta"] = False

    data_volta_calculada = data_ida + timedelta(days=numero_noites)

    if not st.session_state["atualizando_volta"]:
        if st.session_state.get("data_volta") != data_volta_calculada:
            st.session_state["atualizando_volta"] = True
            st.session_state["data_volta"] = data_volta_calculada
            st.rerun()
    else:
        st.session_state["atualizando_volta"] = False

    data_volta = st.date_input(
        "Data de Volta (Check-out):",
        value=st.session_state["data_volta"],
        key="data_volta_input"
    )
    st.session_state["data_volta"] = data_volta

    # ------------------------------------------
    # Controle de atualização de Número de Noites
    # ------------------------------------------
    if "atualizando_noites" not in st.session_state:
        st.session_state["atualizando_noites"] = False

    dias_calculados = (data_volta - data_ida).days

    if not st.session_state["atualizando_noites"]:
        if dias_calculados != numero_noites:
            st.session_state["atualizando_noites"] = True
            st.session_state.numero_noites = dias_calculados
            st.rerun()
    else:
        st.session_state["atualizando_noites"] = False

    # Pernoite
    noites = dias_calculados
    dias = noites + 1
    pernoite_texto = f"{dias} dias e {noites} noites"
    st.text_input("Pernoite:", value=pernoite_texto, key="campo_pernoite", disabled=True)

    # Adultos
    adultos = st.number_input(
        "Adultos:",
        min_value=0,
        max_value=9,
        step=1,
        value=st.session_state.get("adultos", 0),
        key="adultos_input"
    )
    st.session_state["adultos"] = adultos

    # CHD 0 a 5
    chd_0_5 = st.number_input(
        "CHD 0 a 5 anos:",
        min_value=0,
        max_value=5,
        step=1,
        value=st.session_state.get("chd_0_5", 0),
        key="chd_0_5_input"
    )
    st.session_state["chd_0_5"] = chd_0_5

    # CHD 6 a 11
    chd_6_11 = st.number_input(
        "CHD 6 a 11 anos:",
        min_value=0,
        max_value=5,
        step=1,
        value=st.session_state.get("chd_6_11", 0),
        key="chd_6_11_input"
    )
    st.session_state["chd_6_11"] = chd_6_11

    st.markdown("<br>", unsafe_allow_html=True)


    # -------------------------------
    # BLOCO 2 - DESCRIÇÃO DA HOSPEDAGEM
    # -------------------------------

    # Linha divisória
    st.markdown("<hr style='border:1px solid #ccc;'>", unsafe_allow_html=True)

    # Fundo visual leve acima do título
    st.markdown("""
        <div style='background-color:#f9f9ff; padding:8px; border-radius:5px; margin-bottom:5px;'>
        </div>
    """, unsafe_allow_html=True)

    st.header("🏨 Descrição da Hospedagem")
    st.caption("Selecione a cidade onde está localizado o hotel e informe o nome do hotel para buscar uma descrição já cadastrada. Caso o hotel ainda não esteja no sistema, cole abaixo um texto original para que a IA gere uma descrição comercial.")

    try:
        resposta_destinos = requests.get(f"{URL_API_BACKEND}/hoteis/destinos")
        if resposta_destinos.status_code == 200:
            lista_destinos = resposta_destinos.json()
        else:
            lista_destinos = []
    except Exception as e:
        lista_destinos = []

    opcoes_cidades = ["Selecione uma cidade..."] + lista_destinos + ["Cadastrar nova cidade..."]

    cidade_hotel = st.session_state.get("cidade_hotel", "")

    index_cidade = 0
    if cidade_hotel and cidade_hotel in opcoes_cidades:
        index_cidade = opcoes_cidades.index(cidade_hotel)

    cidade_selecionada = st.selectbox("Cidade / Localização do Hotel:", options=opcoes_cidades, index=index_cidade)

    if cidade_selecionada == "Cadastrar nova cidade...":
        cidade_hotel = st.text_input("Digite a nova cidade:", value=cidade_hotel or "")
    elif cidade_selecionada != "Selecione uma cidade...":
        cidade_hotel = cidade_selecionada
    else:
        cidade_hotel = ""

    st.session_state["cidade_hotel"] = cidade_hotel

    # ✅ Mostrar a mensagem de orientação apenas se a cidade já foi escolhida e o hotel ainda não foi digitado
    mostrar_mensagem_busca = False

    if cidade_hotel.strip() != "":
        nome_hotel_digitado = st.session_state.get("nome_hotel", "").strip()
        descricao_hotel_existente = st.session_state.get("descricao_hotel", "").strip()

        if nome_hotel_digitado == "" and descricao_hotel_existente == "":
            mostrar_mensagem_busca = True

    if mostrar_mensagem_busca:
        st.info("ℹ️ Após selecionar a cidade, digite o nome do hotel no campo abaixo e pressione Enter para buscar hotéis já cadastrados.")

    # Campo para o nome do hotel
    if cidade_hotel.strip() != "":
        nome_hotel = st.session_state.get("nome_hotel", "")
        valor_anterior_nome_hotel = nome_hotel

        nome_hotel = st.text_input("🔎 Pesquisar Hotel:", value=nome_hotel, placeholder="Digite o nome do hotel")
        st.session_state["nome_hotel"] = nome_hotel

        if valor_anterior_nome_hotel and nome_hotel.strip() == "":
            st.session_state["nome_hotel"] = ""
            st.session_state["descricao_hotel"] = ""
            st.session_state[f"ia_gerado_{valor_anterior_nome_hotel}"] = None
            st.warning("⚠️ Nome do hotel apagado. Por favor, selecione novamente a cidade antes de continuar para evitar erros de cadastro.")
            st.rerun()

        descricao_hotel = st.session_state.get("descricao_hotel", "")

        if nome_hotel.strip() != "":
            try:
                resposta = requests.get(
                    f"{URL_API_BACKEND}/hoteis",
                    params={"destino": cidade_hotel, "nome": nome_hotel}
                )
                if resposta.status_code == 200:
                    dados_hotel = resposta.json()
                    if dados_hotel and "descricao" in dados_hotel:
                        descricao_hotel = dados_hotel["descricao"]
                        nome_hotel = dados_hotel["nome"]
                        st.session_state["descricao_hotel"] = descricao_hotel
                        st.session_state["nome_hotel"] = nome_hotel
                        st.success("✅ Hotel encontrado no banco e descrição recuperada com sucesso!")
                elif resposta.status_code == 404:
                    st.warning("⚠️ Hotel ainda não cadastrado. Por favor, cole abaixo o texto original do hotel (ex: texto do Booking).")
                else:
                    st.error(f"❌ Erro ao consultar o backend: {resposta.status_code} - {resposta.text}")
            except Exception as e:
                st.error(f"❌ Erro ao conectar com backend: {str(e)}")

            nome_hotel = st.text_input("Nome do Hotel (Corrigido):", value=nome_hotel if nome_hotel.strip() != "" else "")
            st.session_state["nome_hotel"] = nome_hotel

            # ✅ Validação: Nome do hotel deve ter no mínimo 2 palavras
            if nome_hotel.strip() != "":
                partes_nome = nome_hotel.strip().split()
                if len(partes_nome) < 2:
                    st.error("❌ O nome do hotel deve conter pelo menos duas palavras. Exemplo válido: 'Zagaia Resort', 'Hotel Fazenda', etc.")

            if nome_hotel and descricao_hotel.strip() == "":
                texto_original = st.text_area(
                    "📋 Texto Original do Hotel (ex: copiar do Booking ou site do hotel):",
                    value=st.session_state.get("texto_original", "")
                )
                st.session_state["texto_original"] = texto_original

                if texto_original.strip() != "" and st.session_state.get(f"ia_gerado_{nome_hotel}") is None:
                    with st.spinner("🕐 Gerando a descrição comercial do hotel..."):
                        try:
                            resposta = requests.post(
                                f"{URL_API_BACKEND}/hoteis/gerar-descricao",
                                params={"nome": nome_hotel, "destino": cidade_hotel},
                                json={"texto_original": texto_original}
                            )
                            if resposta.status_code == 200:
                                descricao_hotel = resposta.json()["descricao"]
                                st.session_state[f"ia_gerado_{nome_hotel}"] = True
                                st.session_state["descricao_hotel"] = descricao_hotel
                                st.success("✅ Descrição comercial gerada com sucesso pela IA!")
                                st.rerun()
                            else:
                                st.error(f"❌ Erro ao gerar descrição: {resposta.status_code} - {resposta.text}")
                        except Exception as e:
                            st.error(f"❌ Erro ao conectar com backend: {str(e)}")

            descricao_hotel = st.text_area(
                "Descrição Comercial (IA):",
                value=descricao_hotel,
                height=150
            )
            st.session_state["descricao_hotel"] = descricao_hotel

    else:
        st.warning("⚠️ Selecione ou cadastre uma cidade antes de continuar com os dados do hotel.")

    st.markdown("<br>", unsafe_allow_html=True)



    # -------------------------------
    # BLOCO 3 - CONFIGURAÇÃO DO APARTAMENTO E SERVIÇOS
    # -------------------------------

    # Linha divisória
    st.markdown("<hr style='border:1px solid #ccc;'>", unsafe_allow_html=True)

    # Fundo visual leve
    st.markdown("""
        <div style='background-color:#fff8f0; padding:8px; border-radius:5px; margin-bottom:5px;'>
        </div>
    """, unsafe_allow_html=True)

    st.header("🏨 Configuração do Apartamento e Serviços")
    st.caption("Informe os detalhes operacionais da hospedagem, como tipo de acomodação, regime de alimentação, serviços incluídos e valor total.")

    # Quantidade de apartamentos com limite de 1 a 4
    qtd_apartamentos = st.number_input(
        "Quantidade de Apartamentos:",
        min_value=1,
        max_value=4,
        step=1,
        value=st.session_state.get("qtd_apartamentos", 1)
    )
    st.session_state["qtd_apartamentos"] = qtd_apartamentos

    # Campos dinâmicos: Tipo de Apartamento para cada unidade
    tipos_apartamento = []
    for i in range(qtd_apartamentos):
        tipo = st.selectbox(
            f"Tipo de Apartamento {i+1}:",
            ["Standard", "Luxo", "Super Luxo", "Suíte"],
            index=st.session_state.get(f"tipo_apartamento_index_{i}", 0),
            key=f"tipo_apartamento_{i}"
        )
        tipos_apartamento.append(tipo)
        st.session_state[f"tipo_apartamento_index_{i}"] = ["Standard", "Luxo", "Super Luxo", "Suíte"].index(tipo)

    # Campo de acomodação
    acomodacao = st.selectbox(
        "Acomodação:",
        ["Single", "Duplo", "Triplo", "Quadruplo"],
        index=st.session_state.get("acomodacao_index", 1)
    )
    st.session_state["acomodacao_index"] = ["Single", "Duplo", "Triplo", "Quadruplo"].index(acomodacao)

    # Regime de alimentação
    regime_alimentacao = st.selectbox(
        "Regime de Alimentação:",
        ["Sem Café", "Café da Manhã", "Meia Pensão", "Pensão Completa", "All Inclusive"],
        index=st.session_state.get("regime_index", 1)
    )
    st.session_state["regime_index"] = ["Sem Café", "Café da Manhã", "Meia Pensão", "Pensão Completa", "All Inclusive"].index(regime_alimentacao)

    # Serviços inclusos
    opcoes_servicos = [
        "Café da Manhã", "Wi-Fi", "Piscina", "Estacionamento", "Serviço de Quarto",
        "Translado", "Academia", "Área Kids", "SPA", "Bar/Lounge"
    ]
    servicos_inclusos = st.multiselect(
        "Serviços Inclusos:",
        options=opcoes_servicos,
        default=st.session_state.get("servicos_inclusos", []),
        help="Selecione os serviços oferecidos pelo hotel (ex: Wi-Fi, Piscina, Café da Manhã, etc)."
    )
    st.session_state["servicos_inclusos"] = servicos_inclusos

    # Valor total da hospedagem
    valor_total_hospedagem = st.text_input(
        "Valor Total da Hospedagem (R$):",
        value=st.session_state.get("valor_total_hospedagem", ""),
        placeholder="Ex: 1.500,00"
    )
    st.session_state["valor_total_hospedagem"] = valor_total_hospedagem

    # Prazo de cancelamento
    prazo_cancelamento = st.date_input(
        "Prazo de Cancelamento Sem Custo:",
        value=st.session_state.get("prazo_cancelamento", None)
    )
    st.session_state["prazo_cancelamento"] = prazo_cancelamento

    # Função auxiliar para limpar o valor digitado
    def limpar_valor(valor_str):
        try:
            valor_str = valor_str.replace(".", "").replace(",", ".").strip()
            return float(valor_str)
        except:
            return 0.0

    valor_total = limpar_valor(valor_total_hospedagem)

    # Calcular prazo mínimo permitido
    prazo_minimo_dias = 20
    data_limite_cancelamento = data_ida - timedelta(days=prazo_minimo_dias)

    # Simular cálculo de parcelamento para validar se é à vista
    resultado_parcelamento = calcular_parcelamento(data_ida, valor_total)

    # Só valida se o campo prazo_cancelamento foi preenchido
    if prazo_cancelamento:
        if prazo_cancelamento < data_limite_cancelamento:
            pagamento_a_vista = False
            if resultado_parcelamento and resultado_parcelamento.get("parcelas"):
                primeira_parcela = resultado_parcelamento["parcelas"][0]
                if primeira_parcela.get("total_parcelas") == 1:
                    pagamento_a_vista = True

            if not pagamento_a_vista:
                st.error(f"❌ Atenção: O prazo de cancelamento sem custo deve ser no máximo {prazo_minimo_dias} dias antes do check-in.\n\n"
                        f"Exemplo: Para check-in em {data_ida.strftime('%d/%m/%Y')}, o prazo limite é {data_limite_cancelamento.strftime('%d/%m/%Y')}.\n\n"
                        "Só é permitido enviar orçamento fora do prazo para pagamentos à vista.")


  

    # -------------------------------
    # BLOCO 4 - RESULTADO DO PARCELAMENTO
    # -------------------------------

    st.markdown("<hr style='border:1px solid #ccc;'>", unsafe_allow_html=True)

    def limpar_valor(valor_str):
        try:
            valor_str = valor_str.replace(".", "").replace(",", ".").strip()
            return float(valor_str)
        except:
            return 0.0

    nome_hotel = st.session_state.get("nome_hotel", "")
    cidade_hotel = st.session_state.get("cidade_hotel", "")
    qtd_apartamentos = st.session_state.get("qtd_apartamentos", 0)
    data_ida = st.session_state.get("data_ida", None)
    prazo_cancelamento = st.session_state.get("prazo_cancelamento", None)
    acomodacao_index = st.session_state.get("acomodacao_index", None)
    acomodacao = ["Single", "Duplo", "Triplo", "Quadruplo"][acomodacao_index] if acomodacao_index is not None else ""
    valor_total_hospedagem = st.session_state.get("valor_total_hospedagem", "")

    valor_total = limpar_valor(valor_total_hospedagem)

    habilitar_botao = True
    mensagens_erro = []

    if not data_ida:
        habilitar_botao = False
        mensagens_erro.append("❌ Preencha a Data de Ida (Check-in).")

    if not nome_hotel or nome_hotel.strip() == "":
        habilitar_botao = False
        mensagens_erro.append("❌ Preencha o nome do hotel.")

    if not cidade_hotel or cidade_hotel.strip() == "":
        habilitar_botao = False
        mensagens_erro.append("❌ Selecione a cidade do hotel.")

    if valor_total <= 0:
        habilitar_botao = False
        mensagens_erro.append("❌ Informe o Valor Total da Hospedagem.")

    if qtd_apartamentos <= 0:
        habilitar_botao = False
        mensagens_erro.append("❌ Informe a quantidade de apartamentos.")

    prazo_minimo_dias = 20
    if data_ida:
        data_limite_cancelamento = data_ida - timedelta(days=prazo_minimo_dias)

        resultado_parcelamento = calcular_parcelamento(data_ida, valor_total)
        pagamento_a_vista = False
        if resultado_parcelamento and resultado_parcelamento.get("parcelas"):
            primeira_parcela = resultado_parcelamento["parcelas"][0]
            if primeira_parcela.get("total_parcelas") == 1:
                pagamento_a_vista = True

        if prazo_cancelamento and prazo_cancelamento < data_limite_cancelamento and not pagamento_a_vista:
            habilitar_botao = False
            mensagens_erro.append("❌ O prazo de cancelamento está fora do permitido. Só é permitido gerar orçamento fora do prazo para pagamentos à vista.")

    if mensagens_erro:
        for msg in mensagens_erro:
            st.warning(msg)

    col1, col2 = st.columns(2)

    with col1:
        st.header("💳 Resultado do Parcelamento")
        st.caption("Confira abaixo um resumo dos dados do orçamento antes de calcular o parcelamento.")
        st.markdown(f"**Destino:** {cidade_hotel if cidade_hotel else '❌ Não preenchido'}")
        st.markdown(f"**Hotel:** {nome_hotel if nome_hotel else '❌ Não preenchido'}")
        st.markdown(f"**Acomodação:** {acomodacao if acomodacao else '❌ Não preenchido'}")
        st.markdown(f"**Valor Total:** R$ {valor_total:.2f}" if valor_total > 0 else "❌ Valor total não preenchido")
        st.markdown(f"**Data da Viagem (Check-in):** {data_ida.strftime('%d/%m/%Y') if data_ida else '❌ Não preenchido'}")
        st.markdown(f"**Prazo de Cancelamento:** {prazo_cancelamento.strftime('%d/%m/%Y') if prazo_cancelamento else '❌ Não preenchido'}")

        # Desativar botão se campo 'prazo_cancelamento' estiver vazio
        if not prazo_cancelamento:
            habilitar_botao = False
            st.warning("⚠️ Preencha o Prazo de Cancelamento para ativar o cálculo do parcelamento.")

        calcular_button = st.button("🔢 Calcular Parcelamento", disabled=not habilitar_botao)


    resultado = None

    with col2:
        resultado = None

        # Se clicou no botão calcular, calcula e salva
        if calcular_button and habilitar_botao:
            resultado = calcular_parcelamento(data_ida, valor_total)
            st.session_state["resultado_parcelamento"] = resultado

        # Exibe o último resultado salvo, mesmo após o rerun
        resultado_final = resultado or st.session_state.get("resultado_parcelamento")

        if resultado_final:
            if "erro" in resultado_final:
                st.error(resultado_final["erro"])
            else:
                st.success("✅ Parcelamento calculado com sucesso!")
                st.markdown(f"**Parcelamento:** {resultado_final['mensagem']}")

                st.markdown("**Valor das Parcelas:**")
                for parcela in resultado_final["parcelas"]:
                    st.markdown(f"- Parcela {parcela['parcela']}: R$ {parcela['valor']:.2f} - Vencimento: {parcela['vencimento']}")

    # Botão Salvar Orçamento
    if habilitar_botao and st.session_state.get("resultado_parcelamento"):
        col_esq, col_meio, col_dir = st.columns([1, 2, 1])

        with col_meio:
            if st.button("💾 Salvar Orçamento"):
                try:
                    resultado_salvo = st.session_state.get("resultado_parcelamento")

                    # Montagem correta do parcelas_json
                    parcelas_json = []
                    for p in resultado_salvo.get("parcelas", []):
                        if hasattr(p, "dict"):
                            p_dict = p.dict()
                        else:
                            p_dict = p

                        parcelas_json.append({
                            "parcela": p_dict.get("parcela"),
                            "vencimento": p_dict.get("vencimento"),
                            "valor": p_dict.get("valor")
                        })

                    payload = {
                        "tipo_pacote": ["Selecione...", "Hospedagem Bonito", "Hospedagem Brasil", "Pacote Bonito (Hospedagem + Passeios)"][st.session_state.get("tipo_pacote_index", 0)],
                        "destino": ["Bonito", "Nordeste", "Outros"][st.session_state.get("destino_index", 0)],
                        "data_ida": st.session_state.get("data_ida").isoformat(),
                        "data_volta": st.session_state.get("data_volta").isoformat(),
                        "numero_noites": st.session_state.get("numero_noites"),
                        "adultos": st.session_state.get("adultos"),
                        "chd_0_5": st.session_state.get("chd_0_5"),
                        "chd_6_11": st.session_state.get("chd_6_11"),
                        "cidade_hotel": st.session_state.get("cidade_hotel"),
                        "nome_hotel": st.session_state.get("nome_hotel"),
                        "descricao_hotel": st.session_state.get("descricao_hotel"),
                        "qtd_apartamentos": st.session_state.get("qtd_apartamentos"),
                        "acomodacao": ["Single", "Duplo", "Triplo", "Quadruplo"][st.session_state.get("acomodacao_index", 0)],
                        "regime": ["Sem Café", "Café da Manhã", "Meia Pensão", "Pensão Completa", "All Inclusive"][st.session_state.get("regime_index", 0)],
                        "servicos": ", ".join(st.session_state.get("servicos_inclusos", [])),
                        "valor_total": float(st.session_state.get("valor_total_hospedagem").replace(".", "").replace(",", ".")),
                        "prazo_cancelamento": st.session_state.get("prazo_cancelamento").isoformat(),
                        "parcelas_json": parcelas_json,
                        "descricao_parcelamento": resultado_salvo.get("mensagem")
                    }

                    headers = {"Authorization": f"Bearer {st.session_state.token}"}
                    response = requests.post(f"{URL_API_BACKEND}/orcamentos/pre-pago/", json=payload, headers=headers)

                    if response.status_code in [200, 201]:

                        API_BASE = os.getenv("API_BASE", "http://localhost:8000")
                        token = st.session_state.get("token")
                        numero_orcamento = response.json().get("numero_orcamento")

                        st.markdown("<hr style='border:1px solid #ddd;'>", unsafe_allow_html=True)
                        st.markdown("### 🧾 Ações disponíveis para o orçamento gerado")
                        st.markdown("<br>", unsafe_allow_html=True)

                        col1, col2, col3 = st.columns([1, 1, 1])

                        with col1:
                            st.markdown(
                                f"""
                                <a href="{API_BASE}/orcamentos/pre-pago/{numero_orcamento}/html?token={token}" target="_blank">
                                    <button style="background-color:#4CAF50; color:white; padding:10px 16px; border:none; border-radius:8px; font-size:16px; cursor:pointer;">
                                        🔍 Visualizar Orçamento
                                    </button>
                                </a>
                                """,
                                unsafe_allow_html=True
                            )

                        with col2:
                            st.markdown(
                                f"""
                                <a href="{API_BASE}/orcamentos/pre-pago/{numero_orcamento}/pdf?token={token}" download target="_blank">
                                    <button style="
                                        background-color:#2196F3;
                                        color:white;
                                        padding:10px 16px;
                                        border:none;
                                        border-radius:8px;
                                        font-size:16px;
                                        cursor:pointer;">
                                        📥 Download em PDF
                                    </button>
                                </a>
                                """,
                                unsafe_allow_html=True
                            )


                    else:
                        st.error(f"❌ Erro ao salvar orçamento: {response.status_code} - {response.text}")

                except Exception as e:
                    st.error(f"❌ Erro ao tentar salvar orçamento: {str(e)}")


    # -------------------------------
    # BOTÃO FINAL - RESET SELETIVO DO FORMULÁRIO
    # -------------------------------
    st.markdown("<hr style='border:1px solid #ccc;'>", unsafe_allow_html=True)
    col_reset1, col_reset2, col_reset3 = st.columns([1, 2, 1])

    with col_reset2:
        if st.button("🗑️ Limpar Todo o Formulário"):
            chaves_para_limpar = [
                "tipo_pacote_index", "destino_index", "data_ida", "numero_noites", "data_volta", "adultos",
                "chd_0_5", "chd_6_11", "cidade_hotel", "nome_hotel", "descricao_hotel", "qtd_apartamentos",
                "acomodacao_index", "regime_index", "servicos_inclusos", "valor_total_hospedagem",
                "prazo_cancelamento", "resultado_parcelamento", "atualizando_noites", "atualizando_volta"
            ]

            for chave in chaves_para_limpar:
                if chave in st.session_state:
                    del st.session_state[chave]

            st.rerun()
