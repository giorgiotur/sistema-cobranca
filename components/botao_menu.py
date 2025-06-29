import streamlit as st

def botao_menu(label, emoji, destino):
    if st.button(f"{emoji} {label}", key=f"menu_{destino}", use_container_width=True):
        st.session_state.pagina = destino
        st.rerun()