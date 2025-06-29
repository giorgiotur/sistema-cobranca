import streamlit as st
import requests
import re
from dotenv import load_dotenv
import os

load_dotenv()
API_BASE = os.getenv("API_BASE", "http://localhost:8000")

def buscar_cpf_reserva():
    st.title("👤 Responsável pela Reserva")

    token = st.session_state.get("token")
    if not token:
        st.warning("⚠️ Você precisa estar logado.")
        return

    # CPF que veio após criar novo cliente
    cpf_pre_selecionado = st.session_state.get("cpf_reserva")

    # ===== Bloco Centralizado para Input CPF =====
    col_c1, col_input, col_c2 = st.columns([3, 4, 3])
    with col_input:
        cpf_input = st.text_input(
            "Informe o CPF do responsável pela reserva:",
            value=cpf_pre_selecionado or "",
            key="cpf_reserva_input"
        )

    # ===== Botão Buscar Centralizado =====
    _, col_btn, _ = st.columns([4.5, 3, 4.5])
    with col_btn:
        buscar_cliente = st.button("🔎 Buscar CPF", use_container_width=True)

    # ===== Lógica de Busca =====
    if buscar_cliente and cpf_input:
        cpf_limpo = re.sub(r'\D', '', cpf_input)

        if not cpf_limpo or len(cpf_limpo) != 11:
            st.error("❌ CPF inválido. Digite um CPF com 11 dígitos.")
            return

        headers = {"Authorization": f"Bearer {token}"}
        url = f"{API_BASE}/clientes/por-cpf/{cpf_limpo}"

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            cliente = response.json()

            st.success("✅ Cliente encontrado!")

            st.markdown(f"**Nome:** {cliente.get('nome', '—')}")
            st.markdown(f"**CPF:** {cliente.get('cpf', '—')}")
            st.markdown(f"**E-mail:** {cliente.get('email', '—')}")
            st.markdown(f"**Telefone:** {cliente.get('telefone', '—')}")
            st.markdown(f"**CEP:** {cliente.get('cep', '—')}")
            st.markdown(f"**Rua:** {cliente.get('rua', '—')}")
            st.markdown(f"**Número:** {cliente.get('numero', '—')}")
            st.markdown(f"**Complemento:** {cliente.get('complemento', '—')}")
            st.markdown(f"**Bairro:** {cliente.get('bairro', '—')}")
            st.markdown(f"**Cidade:** {cliente.get('cidade', '—')}")
            st.markdown(f"**Estado:** {cliente.get('estado', '—')}")

            # Botão centralizado e estilizado
            col_esq, col_btn, col_dir = st.columns([4.5, 3, 4.5])
            with col_btn:
                if st.button("✅ Confirmar Cliente", use_container_width=True):
                    st.session_state.responsavel_reserva = cliente
                    st.session_state.pagina = "cadastro_viajantes"
                    st.rerun()

        else:
            st.warning("❌ CPF não encontrado no sistema.")
            _, col_cadastrar, _ = st.columns([4.5, 3, 4.5])
            with col_cadastrar:
                if st.button("➕ Cadastrar Novo Cliente", use_container_width=True):
                    st.session_state.cpf_pre_cadastro = cpf_limpo
                    st.session_state.pagina = "novo_cliente"
                    st.rerun()
