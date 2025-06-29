import streamlit as st
import requests
from dotenv import load_dotenv
import os

load_dotenv()
API_BASE = os.getenv("API_BASE", "http://localhost:8000")

def tela_consultar_cliente():
    st.title("🔎 Consultar Cliente")

    if "busca_cliente" not in st.session_state:
        st.session_state.busca_cliente = ""

    st.session_state.pagina_anterior = "consultar_cliente"

    st.markdown("""
    <style>
    div[data-testid="stExpander"] > div:first-child {
        border: none;
        box-shadow: none;
    }
    </style>
    """, unsafe_allow_html=True)

    col_c1, col_input, col_c2 = st.columns([3, 4, 3])
    with col_input:
        termo_busca = st.text_input(
            "🔍 Buscar por CPF ou E-mail",
            key="busca_cliente"
        )

    if termo_busca.strip() and "resultado_clientes" not in st.session_state:
        try:
            resposta = requests.get(
                f"{API_BASE}/clientes/por-cpf-ou-email/{termo_busca.strip()}",
                headers={"Authorization": f"Bearer {st.session_state.token}"}
            )
            if resposta.status_code == 200:
                cliente = resposta.json()
                st.session_state.resultado_clientes = [cliente]
        except Exception as e:
            st.error(f"❌ Erro ao buscar cliente: {e}")

    if termo_busca.strip() == "":
        if "resultado_clientes" in st.session_state:
            del st.session_state.resultado_clientes

    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)

    _, col_btn, _ = st.columns([3, 2, 3])
    with col_btn:
        if st.button("🔎 Buscar Cliente", use_container_width=True, disabled=not termo_busca.strip()):
            try:
                termo_limpo = termo_busca.strip()
                resposta = requests.get(
                    f"{API_BASE}/clientes/por-cpf-ou-email/{termo_limpo}",
                    headers={"Authorization": f"Bearer {st.session_state.token}"}
                )

                if resposta.status_code == 200:
                    cliente = resposta.json()
                    st.session_state.resultado_clientes = [cliente]
                    st.success("✅ Cliente encontrado.")
                    st.rerun()
                elif resposta.status_code == 404:
                    st.warning("❌ Nenhum cliente encontrado com este CPF ou E-mail.")
                else:
                    st.error(f"❌ Erro na busca: {resposta.status_code} - {resposta.text}")
            except Exception as e:
                st.error(f"❌ Erro ao conectar com a API: {e}")

    if "resultado_clientes" in st.session_state:
        clientes = st.session_state.resultado_clientes

        if clientes:
            st.markdown("### 📋 Resultado da Busca:")

            for cliente in clientes:
                with st.expander("", expanded=True):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown(f"**👤 Nome completo:** {cliente.get('nome', '—')}")
                        st.markdown(f"**🆔 CPF:** {cliente.get('cpf', '—')}")
                        st.markdown(f"**📅 Data de Nascimento:** {cliente.get('data_nascimento', '—')}")
                        st.markdown(f"**📞 Telefone:** {cliente.get('telefone', '—')}")
                        st.markdown(f"**✉️ E-mail:** {cliente.get('email', '—')}")
                        st.markdown(f"**📍 CEP:** {cliente.get('cep', '—')}")

                        status_asaas = cliente.get('asaas_status')
                        if (status_asaas or "").lower() == "sucesso":
                            st.info(f"📊 Status Asaas: {status_asaas}")
                        elif not status_asaas:
                            st.error("📊 Status Asaas: ❌ Não processado")
                        else:
                            st.error(f"📊 Status Asaas: {status_asaas}")

                    with col2:
                        st.markdown(f"**🏠 Rua:** {cliente.get('rua', '—')}")
                        st.markdown(f"**🏘️ Bairro:** {cliente.get('bairro', '—')}")
                        st.markdown(f"**🌆 Cidade:** {cliente.get('cidade', '—')}")
                        st.markdown(f"**🗺️ Estado:** {cliente.get('estado', '—')}")
                        st.markdown(f"**🔢 Número:** {cliente.get('numero', '—')}")
                        st.markdown(f"**➕ Complemento:** {cliente.get('complemento', '—')}")

                    col_b1, col_b2, col_b3 = st.columns(3)

                    with col_b1:
                        if st.button("👁️ Ver Detalhes", key=f"ver_detalhes_{cliente.get('id')}", use_container_width=True):
                            st.session_state.cliente_id = cliente.get("id")
                            st.session_state.pagina_anterior = "consultar_cliente"
                            st.session_state.pagina = "detalhes_cliente"
                            st.rerun()

                    with col_b2:
                        if st.button("📄 Serviços Contratados", key=f"servicos_{cliente.get('id')}", use_container_width=True):
                            st.warning("⚠️ Tela de serviços ainda não implementada.")

                    with col_b3:
                        status_asaas_botao = (cliente.get('asaas_status') or "").lower()
                        if status_asaas_botao != "sucesso":
                            if st.button("🔄 Reprocessar Status Asaas", key=f"reprocessar_{cliente.get('id')}", use_container_width=True):
                                try:
                                    resposta = requests.patch(
                                        f"{API_BASE}/clientes/{cliente.get('id')}/reprocessar-status-asaas",
                                        headers={"Authorization": f"Bearer {st.session_state.token}"}
                                    )
                                    if resposta.status_code == 200:
                                        st.success("✅ Reprocessamento concluído.")
                                        del st.session_state.resultado_clientes
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Erro no reprocessamento: {resposta.text}")
                                except Exception as e:
                                    st.error(f"❌ Erro ao conectar com a API: {e}")
