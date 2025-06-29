import streamlit as st
import os
from dotenv import load_dotenv
from utils.navigation import ir_para

load_dotenv()
API_BASE = os.getenv("API_BASE", "http://localhost:8000")

def tela_detalhes_orcamento():
    st.title("🧾 Detalhes do Orçamento")

    token = st.session_state.get("token")
    orcamento_id = st.session_state.get("orcamento_id_visualizacao")

    if not token or not orcamento_id:
        st.warning("❌ Não foi possível carregar o orçamento. Por favor, volte para a tela de consulta.")
        if st.button("🔙 Voltar para Consulta de Orçamentos"):
            ir_para("consultar_orcamento")
        return

    # Monta a URL de visualização
    url_html = f"{API_BASE}/orcamentos/pre-pago/{orcamento_id}/html?token={token}"

    st.markdown("---")
    st.success("✅ Clique no botão abaixo para abrir o orçamento completo numa nova aba do navegador.")

    # Botão que abre nova aba
    if st.button("🔎 Abrir Orçamento em Nova Aba"):
        js = f"window.open('{url_html}')"  # JavaScript simples para abrir nova aba
        st.markdown(f'<script>{js}</script>', unsafe_allow_html=True)

    st.markdown("---")
    if st.button("🔙 Voltar para Consulta de Orçamentos"):
        ir_para("consultar_orcamento")
