import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")

def validar_regras_senha(senha):
    regras = []

    # Tamanho mínimo
    if len(senha) >= 8:
        regras.append(("✅ Pelo menos 8 caracteres", "green"))
    else:
        regras.append(("❌ Pelo menos 8 caracteres", "red"))

    # Letra maiúscula
    if any(c.isupper() for c in senha):
        regras.append(("✅ Pelo menos uma letra maiúscula", "green"))
    else:
        regras.append(("❌ Pelo menos uma letra maiúscula", "red"))

    # Número
    if any(c.isdigit() for c in senha):
        regras.append(("✅ Pelo menos um número", "green"))
    else:
        regras.append(("❌ Pelo menos um número", "red"))

    # Caractere especial
    if any(c in "!@#$%^&*()-_=+[]{}|;:'\\\",.<>?/" for c in senha):
        regras.append(("✅ Pelo menos um caractere especial", "green"))
    else:
        regras.append(("❌ Pelo menos um caractere especial", "red"))

    return regras

def tela_definir_senha():
    st.title("🔐 Definir Nova Senha")

    query_params = st.query_params
    token = query_params.get("token", "")
    primeiro_acesso = st.session_state.get("pagina") == "definir_senha"

    # ✅ Bloqueio caso não seja token nem primeiro acesso
    if not token and not primeiro_acesso:
        st.error("❌ Erro: Token inválido ou fluxo de primeiro acesso não identificado.")
        st.stop()

    # ✅ Define o endpoint correto
    if primeiro_acesso:
        st.markdown("Por segurança, você precisa criar uma nova senha antes de continuar.")
        usuario_id = st.session_state.usuario_id
        endpoint = f"{API_BASE}/usuarios/{usuario_id}/alterar-senha"
        payload_campo = "nova_senha"
    else:
        endpoint = f"{API_BASE}/usuarios/definir-senha/{token}"
        payload_campo = "senha"

    # ===== Formulário de nova senha =====
    nova_senha = st.text_input("Nova senha", type="password")

    # ✅ Regras de senha - Sempre visíveis (mesmo com campo vazio)
    st.markdown("<h4 style='margin-top:20px;'>Requisitos da Senha:</h4>", unsafe_allow_html=True)
    for texto, cor in validar_regras_senha(nova_senha):
        st.markdown(
            f"<div style='color:{cor}; font-size:14px; margin-bottom:4px;'>{texto}</div>",
            unsafe_allow_html=True
        )

    confirmar = st.text_input("Confirme a nova senha", type="password")

    if st.button("Salvar nova senha", use_container_width=True):
        if not nova_senha or not confirmar:
            st.warning("Por favor, preencha todos os campos.")
            return

        if nova_senha != confirmar:
            st.error("❌ As senhas não coincidem.")
            return

        # ✅ Bloqueia se ainda tiver regra em vermelho
        erros = [texto for texto, cor in validar_regras_senha(nova_senha) if cor == "red"]
        if erros:
            st.error("❌ A senha ainda não atende todos os requisitos acima.")
            return

        payload = {payload_campo: nova_senha}

        try:
            resposta = requests.post(endpoint, json=payload)
            if resposta.status_code == 200:
                st.success("✅ Senha alterada com sucesso!")

                if primeiro_acesso:
                    st.session_state.pagina = "Início"
                    st.rerun()
            else:
                erro = resposta.json().get("detail", "Erro ao alterar a senha.")
                st.error(erro)

        except Exception as e:
            st.error(f"Erro de conexão: {e}")
