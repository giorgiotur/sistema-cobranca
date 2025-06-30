import streamlit as st
import requests
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()
API_BASE = os.getenv("API_BASE", "http://localhost:8000")

def consultar_orcamento():
    st.title("📋 Consultar Orçamentos Pré-Pagos")

    token = st.session_state.get("token")

    if not token:
        st.warning("⚠️ Você precisa estar logado para visualizar os orçamentos.")
        return

    # ===== Filtros =====
    col_f1, col_f2, col_f3 = st.columns([3, 3, 2])

    with col_f1:
        destino_filtro = st.text_input("Destino:")

    with col_f2:
        agente_filtro = st.text_input("Agente Criador:")

    with col_f3:
        numero_orcamento_filtro = st.text_input("Número do Orçamento:")

    limit = 10
    page = st.session_state.get("pagina_orcamentos", 1)

    params = {"limit": limit, "page": page}
    if destino_filtro:
        params["destino"] = destino_filtro
    if agente_filtro:
        params["agente"] = agente_filtro
    if numero_orcamento_filtro.strip().isdigit():
        params["numero_orcamento"] = int(numero_orcamento_filtro.strip())

    headers = {"Authorization": f"Bearer {token}"}
    url = f"{API_BASE}/orcamentos/pre-pago/"

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        st.error(f"Erro ao buscar orçamentos: {e}")
        return

    st.markdown(f"**Total de registros:** {data['total_registros']}")
    st.markdown("<hr>", unsafe_allow_html=True)

    # ===== Cabeçalho =====
    header_c1, header_c2, header_c3, header_c4, header_c5, header_c6, header_c7, header_c8 = st.columns([1, 2, 3, 2, 2, 2, 3, 2])

    with header_c1: st.markdown("**#**")
    with header_c2: st.markdown("**Destino**")
    with header_c3: st.markdown("**Hotel**")
    with header_c4: st.markdown("**Valor Total**")
    with header_c5: st.markdown("**Data Criação**")
    with header_c6: st.markdown("**Agente**")
    with header_c7:
        st.markdown("<div style='text-align: center; font-weight: bold;'>Ações</div>", unsafe_allow_html=True)
    with header_c8: 
        st.markdown("<div style='text-align: center; font-weight: bold;'>Reservar</div>", unsafe_allow_html=True)
    
    # ===== Listagem =====
    for orc in data["orcamentos"]:
        col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([1, 2, 3, 2, 2, 2, 3, 2])

        with col1:
            st.write(f"{orc['numero_orcamento']}")

        with col2:
            st.write(orc.get("destino", "—"))

        with col3:
            st.write(orc.get("nome_hotel", "—"))

        with col4:
            valor = f"R$ {orc['valor_total']:.2f}".replace('.', ',') if orc.get("valor_total") else "—"
            st.write(valor)

        with col5:
            data_criacao = orc.get("data_criacao", "")[:10] if orc.get("data_criacao") else "—"
            st.write(data_criacao)

        with col6:
            agente_nome = orc.get("agente", "")
            if agente_nome:
                partes = agente_nome.split()
                if len(partes) >= 2:
                    agente_formatado = f"{partes[0]} {partes[-1]}"
                else:
                    agente_formatado = agente_nome
            else:
                agente_formatado = "—"
            st.write(agente_formatado)

        with col7:
            # 🔍 Verifica se já existe uma reserva vinculada a este orçamento
            possui_reserva = False
            try:
                url_verifica = f"{API_BASE}/reservas/por-orcamento/{orc['id']}"
                resposta = requests.get(url_verifica, headers=headers)
                if resposta.status_code == 200 and resposta.json():
                    possui_reserva = True
            except:
                possui_reserva = False

            col_a1, col_a2, col_a3 = st.columns([1, 1, 1])

            # 👁️ Visualizar
            with col_a1:
                st.markdown(f"""
                    <a href="{API_BASE}/orcamentos/pre-pago/{orc['id']}/html?token={token}" target="_blank" title="Visualizar Orçamento">
                        <button style="
                            background-color: white;
                            border: 1px solid #ccc;
                            border-radius: 6px;
                            padding: 6px 10px;
                            width: 100%;
                            text-align: center;
                            font-size: 14px;">
                            🔍
                        </button>
                    </a>
                """, unsafe_allow_html=True)

            # ⬇️ Download
            with col_a2:
                st.markdown(f"""
                    <a href="{API_BASE}/orcamentos/pre-pago/{orc['id']}/pdf?token={token}" target="_blank" title="Download PDF">
                        <button style="
                            background-color: white;
                            border: 1px solid #ccc;
                            border-radius: 6px;
                            padding: 6px 10px;
                            width: 100%;
                            text-align: center;
                            font-size: 14px;">
                            ⬇️
                        </button>
                    </a>
                """, unsafe_allow_html=True)
            is_admin = st.session_state.get("perfil") == "admin"
            # ❌ Excluir (somente Admin e apenas se não for reserva)
            with col_a3:
                if is_admin and not possui_reserva:
                    if st.button("❌", key=f"excluir_{orc['id']}", use_container_width=True, help="Excluir orçamento."):
                        st.session_state["confirmar_exclusao"] = orc["id"]
                else:
                    mensagem = (
                        "🔒 Apenas administradores podem excluir orçamentos."
                        if not is_admin else
                        "⛔ Este orçamento já virou reserva e não pode ser excluído."
                    )
                    st.markdown(f"""
                        <div title="{mensagem}">
                            <button style="width:100%; height:36px;" disabled>❌</button>
                        </div>
                    """, unsafe_allow_html=True)

            # 🔁 Fora de todas as colunas: renderiza confirmação abaixo da lista

                    

        with col8:
            if possui_reserva:
                if st.button("✅", key=f"vendido_{orc['id']}", help="Orçamento já vendido", use_container_width=True):
                    try:
                        url_cpf = f"{API_BASE}/orcamentos/pre-pago/{orc['id']}/cpf"
                        resp = requests.get(url_cpf, headers=headers)
                        if resp.status_code == 200:
                            st.session_state["cpf_pacote"] = resp.json().get("cpf", "")
                            st.session_state.pagina = "consultar_pacotes"
                            st.rerun()
                        else:
                            st.error("Não foi possível obter o CPF do cliente.")
                    except Exception as e:
                        st.error(f"Erro ao buscar CPF: {e}")
            else:
                if st.button("📅", key=f"reservar_{orc['id']}", help="Reservar Orçamento", use_container_width=True):
                    with st.spinner("Atualizando forma de pagamento..."):
                        try:
                            url_recalculo = f"{API_BASE}/orcamentos/pre-pago/{orc['id']}/recalcular-parcelamento"
                            response = requests.put(url_recalculo, headers=headers)

                            if response.status_code == 200:
                                st.success("Parcelamento atualizado com sucesso!")
                            else:
                                st.warning(f"⚠️ Não foi possível atualizar o parcelamento.\n{response.text}")
                        except Exception as e:
                            st.warning(f"⚠️ Erro ao tentar recalcular o parcelamento: {e}")

                    st.session_state.orcamento_reserva = orc["id"]
                    st.session_state.pagina = "fluxo_reserva"
                    st.rerun()

        
        # ✅ AQUI (fora dos blocos 'with', mas ainda dentro do 'for')            
        if st.session_state.get("confirmar_exclusao") == orc["id"]:
            st.warning(f"⚠️ Confirmar exclusão do Orçamento #{orc['numero_orcamento']}?")
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                if st.button("✅ Confirmar", key=f"confirmar_excluir_{orc['id']}"):
                    try:
                        url_excluir = f"{API_BASE}/orcamentos/pre-pago/{orc['id']}"
                        resp = requests.delete(url_excluir, headers=headers)
                        if resp.status_code == 200:
                            st.success("✅ Orçamento excluído com sucesso!")
                            del st.session_state["confirmar_exclusao"]
                            st.rerun()
                        else:
                            st.error(f"Erro ao excluir: {resp.status_code} - {resp.text}")
                    except Exception as e:
                        st.error(f"Erro ao tentar excluir: {e}")
            with col_c2:
                if st.button("❌ Cancelar", key=f"cancelar_excluir_{orc['id']}"):
                    del st.session_state["confirmar_exclusao"]
                    st.rerun()

                
# Consultar Orçamentos Pré-Pagos

    # ===== Paginação =====
    total_paginas = data.get("total_paginas", 1)
    col_p1, col_p2, col_p3, col_p4 = st.columns([1, 2, 2, 1])

    with col_p1:
        if page > 1:
            if st.button("⬅️ Anterior"):
                st.session_state.pagina_orcamentos = page - 1
                st.rerun()

    with col_p2:
        if st.button("Ir para Última Página"):
            st.session_state.pagina_orcamentos = total_paginas
            st.rerun()

    with col_p3:
        if page < total_paginas:
            if st.button("Próxima ➡️"):
                st.session_state.pagina_orcamentos = page + 1
                st.rerun()

    st.markdown(f"Página **{page}** de **{total_paginas}**")

    # ✅ Fora das colunas
    if st.session_state.get("confirmar_exclusao") == orc["id"]:
        st.warning(f"⚠️ Confirmar exclusão do Orçamento #{orc['numero_orcamento']}?")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            if st.button("✅ Confirmar", key=f"confirmar_excluir_{orc['id']}"):
                try:
                    url_excluir = f"{API_BASE}/orcamentos/pre-pago/{orc['id']}"


                    resp = requests.delete(url_excluir, headers=headers)
                    if resp.status_code == 200:
                        st.success("✅ Orçamento excluído com sucesso!")
                        del st.session_state["confirmar_exclusao"]
                        st.rerun()
                    else:
                        st.error(f"Erro ao excluir: {resp.status_code} - {resp.text}")
                except Exception as e:
                    st.error(f"Erro ao tentar excluir: {e}")
        with col_c2:
            if st.button("❌ Cancelar", key=f"cancelar_excluir_{orc['id']}"):
                del st.session_state["confirmar_exclusao"]
                st.rerun()
