import streamlit as st

def ir_para(pagina, **kwargs):
    st.session_state.pagina = pagina
    for chave, valor in kwargs.items():
        st.session_state[chave] = valor
    st.rerun()
