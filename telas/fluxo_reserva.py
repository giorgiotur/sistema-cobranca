import streamlit as st
import requests
import re
from dotenv import load_dotenv
import os
from datetime import date
from utils.formatters import formatar_cpf
from datetime import datetime
import datetime as datetime_module
import locale
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

def parse_data_segura(data_str):
    """
    Tenta converter uma string de data para datetime, aceitando dois formatos:
    - 'yyyy-mm-dd' (formato ISO/Asaas)
    - 'dd/mm/yyyy' (formato brasileiro)
    """
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime_module.datetime.strptime(data_str, fmt)
        except:
            continue
    raise ValueError(f"Formato de data inválido: {data_str}")

load_dotenv()
API_BASE = os.getenv("API_BASE", "http://localhost:8000")

def fluxo_reserva():
    st.title("📝 Fluxo de Reserva de Orçamento")

    token = st.session_state.get("token")
    orcamento_id = st.session_state.get("orcamento_reserva")

    if not token or not orcamento_id:
        st.warning("⚠️ Orçamento não selecionado. Volte e selecione um orçamento primeiro.")
        return

    headers = {"Authorization": f"Bearer {token}"}

    # Controle de etapa
    if "etapa_reserva" not in st.session_state:
        st.session_state.etapa_reserva = 1

    etapa = st.session_state.etapa_reserva

    # ==========================
    # ETAPA 1 - Busca do CPF
    # ==========================
    if etapa == 1:
        st.subheader("1️⃣ Identificação do Responsável pela Reserva")

        # ===== Validação do ID do Orçamento =====
        orcamento_id = st.session_state.get("orcamento_reserva")
        if not orcamento_id:
            st.warning("⚠️ Nenhum orçamento selecionado. Volte e escolha um orçamento antes de iniciar a reserva.")
            return

        # ===== Input CPF =====
        col_esq, col_input, col_dir = st.columns([3, 4, 3])
        with col_input:
            cpf_input = st.text_input("Informe o CPF do cliente pagador:", key="cpf_reserva_input")

        _, col_btn, _ = st.columns([4.5, 3, 4.5])
        with col_btn:
            if st.button("🔎 Buscar Cliente"):
                cpf_limpo = re.sub(r'\D', '', cpf_input)
                url_cliente = f"{API_BASE}/clientes/por-cpf/{cpf_limpo}"
                try:
                    response = requests.get(url_cliente, headers=headers)
                    if response.status_code == 200:
                        cliente = response.json()

                        # ✅ Salvar o cliente_id no session_state
                        st.session_state.cliente_id_reserva = cliente.get("id")

                        # ✅ Salvar o cliente completo como responsável
                        st.session_state.responsavel_reserva = cliente
                        st.success(f"✅ Cliente encontrado: {cliente.get('nome')}")
                    else:
                        st.warning("❌ CPF não encontrado. Cadastre o cliente antes de prosseguir.")
                except Exception as e:
                    st.error(f"Erro ao buscar cliente: {e}")

        # ===== Se cliente encontrado, buscar orçamento também =====
        if st.session_state.get("responsavel_reserva"):
            cliente = st.session_state.responsavel_reserva

            # Buscar orçamento
            url_orcamento = f"{API_BASE}/orcamentos/pre-pago/{orcamento_id}"
            try:
                response = requests.get(url_orcamento, headers=headers)
                response.raise_for_status()
                orcamento = response.json()
            except Exception as e:
                st.error(f"Erro ao buscar orçamento: {e}")
                return

            col1, col2 = st.columns(2)

            # ===== COLUNA 1 - Dados do Pagante =====
            with col1:
                st.markdown("### 👤 Dados do Pagante (Responsável)")
                st.markdown(f"**Nome:** {cliente.get('nome', '—')}")
                st.markdown(f"**CPF:** {cliente.get('cpf', '—')}")
                st.markdown(f"**📅 Data de Nascimento:** {cliente.get('data_nascimento', '—')}")
                st.markdown(f"**E-mail:** {cliente.get('email', '—')}")
                st.markdown(f"**Telefone:** {cliente.get('telefone', '—')}")
                st.markdown(f"**CEP:** {cliente.get('cep', '—')}")
                st.markdown(f"**Rua:** {cliente.get('rua', '—')}")
                st.markdown(f"**Número:** {cliente.get('numero', '—')}")
                st.markdown(f"**Complemento:** {cliente.get('complemento', '—')}")
                st.markdown(f"**Bairro:** {cliente.get('bairro', '—')}")
                st.markdown(f"**Cidade:** {cliente.get('cidade', '—')}")
                st.markdown(f"**Estado:** {cliente.get('estado', '—')}")

            # ===== COLUNA 2 - Resumo do Orçamento =====
            with col2:
                st.markdown("### 🏨 O que vamos reservar")
                st.markdown(f"**Número do Orçamento:** {orcamento.get('numero_orcamento', '—')}")
                st.markdown(f"**Destino:** {orcamento.get('destino', '—')}")
                st.markdown(f"**Período:** {orcamento.get('data_ida', '—')} até {orcamento.get('data_volta', '—')}")
                st.markdown(f"**Data Check-in:** {orcamento.get('data_ida', '—')}")
                st.markdown(f"**Data Check-out:** {orcamento.get('data_volta', '—')}")
                st.markdown(f"**Adultos:** {orcamento.get('adultos', 0)}")

                if orcamento.get('chd_0_5', 0) > 0:
                    st.markdown(f"**Crianças 0 a 5 anos:** {orcamento.get('chd_0_5')}")

                if orcamento.get('chd_6_11', 0) > 0:
                    st.markdown(f"**Crianças 6 a 11 anos:** {orcamento.get('chd_6_11')}")

                st.markdown(f"**Hotel:** {orcamento.get('nome_hotel', '—')}")
                st.markdown(f"**Regime:** {orcamento.get('regime', '—')}")
                st.markdown(f"**Acomodação:** {orcamento.get('acomodacao', '—')}")
                valor_raw = orcamento.get("valor_total", 0)
                try:
                    valor = float(valor_raw)
                except:
                    valor = 0.0

                valor_formatado = locale.currency(valor, grouping=True, symbol=True)  # Ex: R$ 21.000,00
                st.markdown(f"**Valor Total:** {valor_formatado}")


            # ===== BOTÕES: REINICIAR e PRÓXIMO =====
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 2, 3])

            with col1:
                if st.button("🔄 Reiniciar Reserva"):
                    chaves_para_limpar = [
                        "etapa_reserva",
                        "cliente_id_reserva",
                        "responsavel_reserva",
                        "orcamento_reserva",
                        "viajantes_reserva",
                        "operadora_reserva",
                        "numero_reserva_operadora",
                        "observacoes_reserva"
                    ]
                    for chave in dict(st.session_state):
                        if chave in chaves_para_limpar:
                            del st.session_state[chave]

                    st.success("🔁 Reserva reiniciada. Redirecionando para consulta...")
                    st.session_state.pagina = "consultar_orcamento"  # ✅ Navegação correta para sua estrutura
                    st.rerun()

            with col3:
                if st.button("👉 Próximo"):
                    st.session_state.etapa_reserva = 2
                    st.rerun()



    # ==========================
    # ETAPA 2 - Viajantes
    # ==========================
    elif etapa == 2:
        st.subheader("2️⃣ Cadastro dos Viajantes")

        # Buscar o orçamento
        url_orcamento = f"{API_BASE}/orcamentos/pre-pago/{orcamento_id}"
        response = requests.get(url_orcamento, headers=headers)
        orcamento = response.json()

        total_adultos = orcamento.get("adultos", 0)
        total_0_5 = orcamento.get("chd_0_5", 0)
        total_6_11 = orcamento.get("chd_6_11", 0)
        total_viajantes = total_adultos + total_0_5 + total_6_11

        # Inicializar ou atualizar a lista de viajantes
        if ("viajantes_reserva" not in st.session_state 
            or len(st.session_state.viajantes_reserva) != total_viajantes):
            st.session_state.viajantes_reserva = []
            for idx in range(total_viajantes):
                if idx == 0 and st.session_state.get("responsavel_reserva"):
                    nome = st.session_state.responsavel_reserva.get("nome", "")
                    partes = nome.strip().split(" ", 1)
                    primeiro_nome = partes[0] if len(partes) >= 1 else ""
                    ultimo_nome = partes[1] if len(partes) >= 2 else ""
                    st.session_state.viajantes_reserva.append({
                        "primeiro_nome": primeiro_nome,
                        "ultimo_nome": ultimo_nome,
                        "cpf": st.session_state.responsavel_reserva.get("cpf", ""),
                        "data_nascimento": st.session_state.responsavel_reserva.get("data_nascimento", "")
                    })
                else:
                    st.session_state.viajantes_reserva.append({
                        "primeiro_nome": "",
                        "ultimo_nome": "",
                        "cpf": "",
                        "data_nascimento": ""
                    })

        # Exibir campos para cada viajante
        for idx, viajante in enumerate(st.session_state.viajantes_reserva):
            if idx < total_adultos:
                titulo_viajante = f"Nome Viajante {idx + 1}"
            elif idx < total_adultos + total_0_5:
                titulo_viajante = f"Criança 0 a 5 anos ({idx + 1 - total_adultos})"
            else:
                titulo_viajante = f"Criança 6 a 11 anos ({idx + 1 - total_adultos - total_0_5})"

            st.markdown(f"### {titulo_viajante}")

            col1, col2 = st.columns(2)
            with col1:
                viajante["primeiro_nome"] = st.text_input(
                    f"Input{idx + 1} : Primeiro Nome",
                    value=viajante["primeiro_nome"],
                    placeholder="Digite o primeiro nome",
                    key=f"primeiro_nome_{idx}_etapa_{etapa}"
                )
            with col2:
                viajante["ultimo_nome"] = st.text_input(
                    f"Input{idx + 1} : Último Nome",
                    value=viajante["ultimo_nome"],
                    placeholder="Digite o último nome",
                    key=f"ultimo_nome_{idx}_etapa_{etapa}"
                )
            col3, col4 = st.columns(2)
            with col3:
                cpf_digitado = st.text_input(
                    f"CPF Viajante {idx + 1}",
                    value=formatar_cpf(viajante.get("cpf", "")),
                    placeholder="Digite o CPF",
                    key=f"cpf_{idx}_etapa_{etapa}"
                )

                cpf_limpo = re.sub(r'\D', '', cpf_digitado)
                if len(cpf_limpo) == 11:
                    viajante["cpf"] = cpf_limpo
                else:
                    viajante["cpf"] = ""
                    st.warning(f"⚠️ CPF inválido para o Viajante {idx + 1}. Deve conter 11 dígitos.")

            with col4:
                data_input = st.text_input(
                    f"Data de Nascimento Viajante {idx + 1} (dd/mm/aaaa)",
                    value=datetime_module.datetime.strptime(viajante["data_nascimento"], "%Y-%m-%d").strftime("%d/%m/%Y") if viajante.get("data_nascimento") else "",
                    placeholder="Digite a data de nascimento",
                    key=f"data_nascimento_{idx}"
                )
                if re.fullmatch(r"\d{8}", data_input):
                    data_input = f"{data_input[:2]}/{data_input[2:4]}/{data_input[4:]}"
                    st.info(f"✅ Data formatada automaticamente: {data_input}")
                padrao_data = r"^\d{2}/\d{2}/\d{4}$"
                if re.match(padrao_data, data_input):
                    try:
                        data_obj = datetime_module.datetime.strptime(data_input, "%d/%m/%Y").date()
                        viajante["data_nascimento"] = data_obj.strftime("%Y-%m-%d")
                    except ValueError:
                        st.error(f"❌ Data inválida para Viajante {idx + 1}.")
                        viajante["data_nascimento"] = None
                else:
                    if data_input.strip() != "":
                        st.warning(f"⚠️ Informe a data no formato dd/mm/aaaa para o Viajante {idx + 1}.")
                    viajante["data_nascimento"] = None
            st.markdown("---")

        # Travar adição manual de mais viajantes
        if len(st.session_state.viajantes_reserva) >= total_viajantes:
            st.info(f"Limite de {total_viajantes} viajantes atingido. Não é possível adicionar mais.")

        # Botões de navegação
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Voltar"):
                st.session_state.etapa_reserva = 1
                st.rerun()
        with col2:
            if st.button("👉 Próximo", key="proximo_viajantes"):
                faltando = []
                for idx, v in enumerate(st.session_state.viajantes_reserva):
                    if not all([v.get("primeiro_nome"), v.get("ultimo_nome"), v.get("cpf"), v.get("data_nascimento")]):
                        faltando.append(str(idx + 1))
                if faltando:
                    st.error(f"❌ Preencha todos os dados dos seguintes viajantes: {', '.join(faltando)}")
                else:
                    st.session_state.etapa_reserva = 3
                    st.rerun()



    # ==========================
    # ETAPA 3 - Resumo + Operadora
    # ==========================
    elif etapa == 3:
        st.subheader("3️⃣ Resumo da Reserva + Dados da Operadora")

        # ✅ Buscar os dados do orçamento
        url_orcamento = f"{API_BASE}/orcamentos/pre-pago/{orcamento_id}"
        response = requests.get(url_orcamento, headers=headers)

        if response.status_code == 200:
            orcamento = response.json()
        else:
            st.error(f"Erro ao buscar orçamento: {response.status_code} - {response.text}")
            st.stop()

        # ✅ Exibir informações do orçamento
        st.markdown(f"**Destino:** {orcamento.get('destino', '—')}")
        st.markdown(f"**Hotel:** {orcamento.get('nome_hotel', '—')}")
        st.markdown(f"**Check-in:** {orcamento.get('data_ida', '—')}")
        st.markdown(f"**Check-out:** {orcamento.get('data_volta', '—')}")
        valor_raw = orcamento.get("valor_total", 0)
        try:
            valor = float(valor_raw)
        except:
            valor = 0.0

        valor_formatado = locale.currency(valor, grouping=True, symbol=True)  # Ex: R$ 21.000,00
        st.markdown(f"**Valor Total:** {valor_formatado}")
        st.markdown(f"**Parcelamento:** {orcamento.get('descricao_parcelamento', '—')}")

        # ✅ Exibir parcelas (se houver)
        parcelas = orcamento.get("parcelas_json", [])
        if parcelas:
            st.markdown("### 📋 Parcelas do Orçamento")
            for parcela in parcelas:
                num = parcela.get("parcela", "")
                venc = parcela.get("vencimento", "")
                try:
                    valor = float(parcela.get("valor", 0))
                except:
                    valor = 0.0
                valor_formatado = locale.currency(valor, grouping=True, symbol=True)  # R$ 5.250,00
                st.markdown(f"**Parcela {num} - Vencto: {venc}**: {valor_formatado}")

        st.markdown("---")

        # ✅ Seleção da Operadora
        operadora_opcoes = ["E-Htl", "BestBuyHotel"]
        operadora = st.selectbox(
            "Nome da Operadora (onde será feita a reserva)",
            options=operadora_opcoes,
            index=0,
            key="input_operadora_reserva"
        )
        st.session_state.operadora_reserva = operadora

        # ✅ Exibir o Prazo de Cancelamento (não editável)
        prazo_cancelamento = orcamento.get("prazo_cancelamento", "—")
        st.text_input(
            "Prazo de Cancelamento (informado no orçamento)",
            value=prazo_cancelamento,
            disabled=True
        )

        # ✅ Número da Reserva na Operadora (campo obrigatório)
        numero_reserva = st.text_input(
            "Número da Reserva na Operadora (obrigatório após confirmação com a operadora)",
            key="input_numero_reserva_operadora",
            placeholder="Ex: 123456 / Código da Operadora"
        )
        if numero_reserva:
            st.session_state.numero_reserva_operadora = numero_reserva

        # ✅ Observações internas
        observacoes = st.text_area(
            "Observações Internas (opcional)",
            key="input_observacoes_reserva"
        )
        st.session_state.observacoes_reserva = observacoes

        # ✅ Navegação
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Voltar"):
                st.session_state.etapa_reserva = 2
                st.rerun()
        with col2:
            if st.button("👉 Próximo", key="proximo_operadora"):
                erros = []
                if not numero_reserva:
                    erros.append("número da reserva na operadora")
                if not operadora:
                    erros.append("nome da operadora")

                if erros:
                    st.warning(f"⚠️ Por favor, preencha corretamente os campos obrigatórios: {', '.join(erros)}.")
                else:
                    st.session_state.etapa_reserva = 4
                    st.rerun()


    # ==========================
    # ETAPA 4 - Finalização
    # ==========================
    elif etapa == 4:
        st.subheader("4️⃣ Finalização da Reserva")

        # ✅ Buscar novamente o orçamento para garantir dados atualizados
        url_orcamento = f"{API_BASE}/orcamentos/pre-pago/{orcamento_id}"
        try:
            response = requests.get(url_orcamento, headers=headers)
            response.raise_for_status()
            orcamento = response.json()
        except Exception as e:
            st.error(f"❌ Erro ao buscar orçamento: {e}")
            return

        # ✅ Garantir campo 'descricao' nas parcelas
        parcelas_payload = []
        for parcela in orcamento.get("parcelas_json", []):
            try:
                valor_float = float(parcela.get("valor") or 0)
            except:
                valor_float = 0.0

            vencimento_raw = parcela.get("vencimento", "")
            if not vencimento_raw:
                st.error(f"❌ Erro: Parcela {parcela.get('parcela')} está sem data de vencimento. Corrija o orçamento antes de prosseguir.")
                st.stop()

            # Se o vencimento vier no formato dd/mm/aaaa, converter para yyyy-mm-dd
            try:
                if "/" in vencimento_raw:
                    vencimento_convertido = datetime_module.datetime.strptime(vencimento_raw, "%d/%m/%Y").strftime("%Y-%m-%d")
                else:
                    vencimento_convertido = vencimento_raw  # Já deve estar no formato correto
            except Exception as e:
                st.error(f"❌ Data de vencimento inválida na parcela {parcela.get('parcela')}: {vencimento_raw}")
                st.stop()

            parcelas_payload.append({
                "parcela": parcela.get("parcela"),
                "vencimento": vencimento_convertido,
                "valor": valor_float,
                "descricao": f"Parcela {parcela.get('parcela')} - Vencto: {vencimento_raw}"
            })


        # ✅ Montar o JSON de envio para o backend
        reserva_payload = {
            "orcamento_id": orcamento_id,
            "cliente_id": st.session_state.get("cliente_id_reserva"),
            "pagante_id": st.session_state.get("cliente_id_reserva"),  # ✅ NOVO campo obrigatório
            "operadora": st.session_state.get("operadora_reserva"),
            "numero_reserva_operadora": st.session_state.get("numero_reserva_operadora"),
            "observacoes": st.session_state.get("observacoes_reserva", ""),
            "parcelas_json": parcelas_payload,
            "passageiros": st.session_state.get("viajantes_reserva", [])  # ✅ inclui lista de viajantes

        }

        # ✅ Resumo visual da reserva
        st.markdown("### ✅ Resumo da Reserva")
        st.markdown(f"**Número do Orçamento:** {orcamento.get('numero_orcamento', '—')}")
        st.markdown(f"**Destino:** {orcamento.get('destino', '—')}")
        st.markdown(f"**Hotel:** {orcamento.get('nome_hotel', '—')}")
        st.markdown(f"**Check-in:** {orcamento.get('data_ida', '—')}")
        st.markdown(f"**Check-out:** {orcamento.get('data_volta', '—')}")
        valor_raw = orcamento.get("valor_total", 0)
        try:
            valor = float(valor_raw)
        except:
            valor = 0.0

        valor_formatado = locale.currency(valor, grouping=True, symbol=True)  # Ex: R$ 21.000,00
        st.markdown(f"**Valor Total:** {valor_formatado}")


        # ✅ Parcelas (se houver)
        if parcelas_payload:
            st.markdown("### 📋 Parcelas que serão geradas:")
            for parcela in parcelas_payload:
                try:
                    valor = float(parcela.get("valor", 0))
                except:
                    valor = 0.0
                valor_formatado = locale.currency(valor, grouping=True, symbol=True)
                st.markdown(f"**Parcela {parcela['parcela']} - Vencto: {parcela['vencimento']}**: {valor_formatado}")

        # ✅ Outras informações da reserva
        st.markdown(f"**Operadora:** {st.session_state.get('operadora_reserva', '—')}")
        st.markdown(f"**Número Reserva Operadora:** {st.session_state.get('numero_reserva_operadora', '—')}")
        st.markdown(f"**Observações:** {st.session_state.get('observacoes_reserva', '—')}")

        # ✅ Botões de ação
        # 🔹 Botões Horizontais: Voltar | Finalizar | Abrir Contrato
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("⬅️ Voltar"):
                st.session_state.etapa_reserva = 3
                st.rerun()

        with col2:
            if st.button("🏁 Finalizar Reserva"):
                with st.spinner("Salvando a reserva..."):
                    try:
                        url_reserva = f"{API_BASE}/reservas/"
                        resposta = requests.post(url_reserva, headers=headers, json=reserva_payload)

                        if resposta.status_code in [200, 201]:
                            reserva_id = resposta.json().get("id")
                            st.success(f"✅ Reserva criada com sucesso! ID: {reserva_id}")
                            st.session_state["reserva_id_criada"] = reserva_id
                            st.session_state["exibir_boletos_gerados"] = True
                            st.rerun()
                        else:
                            st.error(f"❌ Erro ao criar reserva: {resposta.status_code} - {resposta.text}")
                    except Exception as e:
                        st.error(f"❌ Erro inesperado ao finalizar reserva: {e}")

        with col3:
            if st.session_state.get("reserva_id_criada"):
                reserva_id = st.session_state["reserva_id_criada"]
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.markdown(
                        f'<a href="http://localhost:8000/reservas/{reserva_id}/contrato?formato=html" target="_blank">'
                        f'📝 <b>Visualizar Contrato</b></a>',
                        unsafe_allow_html=True
                    )

                with col2:
                    st.markdown(
                        f'<a href="http://localhost:8000/reservas/{reserva_id}/contrato?formato=pdf" target="_blank">'
                        f'⬇️ <b>Baixar PDF</b></a>',
                        unsafe_allow_html=True
                    )

                with col3:
                    if st.button("❌ Fechar"):
                        chaves_para_limpar = [
                            "etapa_reserva",
                            "cliente_id_reserva",
                            "responsavel_reserva",
                            "orcamento_reserva",
                            "viajantes_reserva",
                            "operadora_reserva",
                            "numero_reserva_operadora",
                            "observacoes_reserva",
                            "reserva_id_criada",
                            "exibir_boletos_gerados"
                        ]

                        for chave in list(st.session_state.keys()):
                            if chave in chaves_para_limpar:
                                del st.session_state[chave]
                        st.success("✅ Fluxo de reserva finalizado.")
                        st.session_state.pagina = "consultar_orcamento"
                        st.rerun()


                        
        # 🔄 Buscar boletos do Asaas para o cliente pagador (com filtro por reserva atual)
        if st.session_state.get("exibir_boletos_gerados") and st.session_state.get("reserva_id_criada"):
            reserva_id = st.session_state["reserva_id_criada"]
            base_asaas_url = os.getenv("ASAAS_API_BASE", "https://sandbox.asaas.com")
            url_boletos = f"{base_asaas_url}/api/v3/payments?externalReference={reserva_id}"

            headers_asaas = {
                "Content-Type": "application/json",
                "access_token": os.getenv("ASAAS_API_KEY")
            }

            try:
                response_boletos = requests.get(url_boletos, headers=headers_asaas)
                if response_boletos.status_code == 200:
                    boletos = response_boletos.json().get("data", [])
                    
                    # ✅ Ordenar por data de vencimento (mais próximo primeiro)
                    boletos.sort(key=lambda b: datetime.strptime(b.get("dueDate", "2100-12-31"), "%Y-%m-%d"))

                    if boletos:
                        st.markdown("### 📄 Boletos Gerados para esta Reserva")
                        st.markdown("""
                            <style>
                                table { width: 100%; border-collapse: collapse; font-family: sans-serif; margin-top: 1em; }
                                th, td { padding: 10px; border: 1px solid #ddd; text-align: left; }
                                th { background-color: #f5f5f5; }
                                td.acao a { margin-right: 8px; text-decoration: none; font-size: 14px; }
                            </style>
                        """, unsafe_allow_html=True)

                        tabela_html = "<table><thead><tr><th>Nome</th><th>Valor</th><th>Descrição</th><th>Forma de pagamento</th><th>Data de vencimento</th><th>Ações</th></tr></thead><tbody>"
                        for b in boletos:
                            nome = st.session_state.responsavel_reserva.get("nome", "—")
                            valor = f"R$ {float(b['value']):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                            desc = b.get("description", "—")
                            tipo = b.get("billingType", "—")
                            venc = b.get("dueDate", "—")
                            url = b.get("invoiceUrl", "#")
                            acoes = f"""
                                <td class='acao'>
                                    <a href="{url}" target="_blank" title="Imprimir">🖨️</a>
                                    <a href="{url}" target="_blank" title="Download">⬇️</a>
                                </td>
                            """
                            tabela_html += f"<tr><td>{nome}</td><td>{valor}</td><td>{desc}</td><td>{tipo}</td><td>{venc}</td>{acoes}</tr>"
                        tabela_html += "</tbody></table>"
                        st.markdown(tabela_html, unsafe_allow_html=True)
                    else:
                        st.info("Nenhum boleto encontrado para esta reserva.")
                else:
                    st.warning(f"Erro ao buscar boletos no Asaas: {response_boletos.status_code}")
            except Exception as e:
                st.error(f"Erro inesperado ao consultar boletos: {e}")

# 🔹 Botão vermelho no final da tela para limpar tudo
st.markdown("---")
if st.session_state.get("reserva_id_criada"):
    if st.button("❌ Fechar e voltar"):
        chaves_para_limpar = [
            "etapa_reserva",
            "cliente_id_reserva",
            "responsavel_reserva",
            "orcamento_reserva",
            "viajantes_reserva",
            "operadora_reserva",
            "numero_reserva_operadora",
            "observacoes_reserva",
            "reserva_id_criada",
            "exibir_boletos_gerados"
        ]
        for chave in chaves_para_limpar:
            if chave in st.session_state:
                del st.session_state[chave]
        st.success("✅ Fluxo de reserva finalizado.")
        st.session_state.pagina = "consultar_orcamento"
        st.rerun()
