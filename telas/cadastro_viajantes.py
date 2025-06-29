import streamlit as st
import requests
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()
API_BASE = os.getenv("API_BASE", "http://localhost:8000")

def cadastro_viajantes():
    st.title("🧳 Cadastro de Viajantes")

    token = st.session_state.get("token")
    orcamento_id = st.session_state.get("orcamento_reserva")

    if not token or not orcamento_id:
        st.warning("⚠️ Não foi possível localizar o orçamento selecionado.")
        return

    headers = {"Authorization": f"Bearer {token}"}
    url = f"{API_BASE}/orcamentos/pre-pago/{orcamento_id}"

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        orcamento = response.json()
    except Exception as e:
        st.error(f"Erro ao carregar o orçamento: {e}")
        return

    # ===== Definir número de PAX previsto =====
    total_pax = orcamento.get("adultos", 0) + orcamento.get("chd_0_5", 0) + orcamento.get("chd_6_11", 0)

    # ===== Inicializar lista de viajantes na sessão =====
    if "viajantes_reserva" not in st.session_state or not st.session_state.viajantes_reserva:
        st.session_state.viajantes_reserva = []
        for i in range(total_pax):
            st.session_state.viajantes_reserva.append({
                "nome": "",
                "cpf": "",
                "data_nascimento": ""
            })

    # ===== Exibir formulário de cada viajante =====
    for idx, viajante in enumerate(st.session_state.viajantes_reserva):
        st.markdown(f"### Viajante {idx + 1}")

        viajante["nome"] = st.text_input(f"Nome do Viajante {idx + 1}", value=viajante["nome"], key=f"nome_{idx}")
        viajante["cpf"] = st.text_input(f"CPF do Viajante {idx + 1}", value=viajante["cpf"], key=f"cpf_{idx}")
        viajante["data_nascimento"] = st.date_input(
            f"Data de Nascimento do Viajante {idx + 1}",
            value=datetime.today().date() if not viajante["data_nascimento"] else datetime.strptime(viajante["data_nascimento"], "%Y-%m-%d").date(),
            key=f"data_nascimento_{idx}"
        ).strftime("%Y-%m-%d")

        col_del, _ = st.columns([1, 5])
        with col_del:
            if st.button(f"❌ Remover Viajante {idx + 1}", key=f"remover_{idx}"):
                st.session_state.viajantes_reserva.pop(idx)
                st.rerun()

        st.markdown("---")
