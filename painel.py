import streamlit as st  # ✅ Linha correta

# PRIMEIRA LINHA do código
st.set_page_config(page_title="Sistema de Cobrança", layout="wide")

query_params = st.query_params

# Se a URL tiver ?pagina=..., atualiza a página ativa
if "pagina" not in st.session_state and "pagina" in query_params:
    st.session_state.pagina = query_params["pagina"]

# Se ainda não tiver página definida, define como menu principal
if "pagina" not in st.session_state:
    st.session_state.pagina = "menu"

import requests
import os
import re
import streamlit.components.v1 as components
import time
import base64
from dotenv import load_dotenv
from pathlib import Path
from streamlit_cookies_manager import CookieManager
from utils.formatters import formatar_cpf, formatar_telefone, formatar_cep
from utils.validators import validar_cpf, validar_telefone, validar_cep, validar_email
from utils.endereco import buscar_cep
from components.menu_lateral import menu_lateral
from utils.navigation import ir_para
from telas.consultar_cliente import tela_consultar_cliente
from telas.novo_cliente import tela_novo_cliente
from telas.meus_dados import tela_meus_dados
from telas.novo_usuario import tela_novo_usuario
from telas.definir_senha import tela_definir_senha
from telas.lista_usuarios import tela_lista_usuarios
from telas.detalhes_cliente import tela_detalhes_cliente
from telas.orcamento_pre_pago import tela_orcamento_pre_pago
from telas import consultar_orcamento
from telas import detalhes_orcamento
from telas.empresa import tela_empresa
from telas.consultar_pacote_view import tela_consultar_pacotes
import streamlit as st
st.write("Versão atual do Streamlit:", st.__version__)

# ===== CONFIGURAÇÕES =====
load_dotenv()
API_BASE = "http://127.0.0.1:8000"

# ===== COOKIES =====
cookies = CookieManager()

if not cookies.ready():
    st.stop()

# ✅ BLOQUEIO TOTAL de primeiro acesso - antes de tudo!
if st.session_state.get("token") and st.session_state.get("pagina") == "definir_senha":
    tela_definir_senha()
    st.stop()

# ===== CSS GLOBAL =====
st.markdown("""
<style>
/* 🎯 Barra superior fixa */
.top-bar {
    background-color: #0033cc;
    height: 80px;
    display: flex;
    align-items: center;
    justify-content: center;
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    z-index: 999;
}

/* ✅ Botão da tela de login */
div.botao-login div.stButton > button:first-child {
    background-color: #28a745;
    color: white;
    font-size: 14px;
    font-weight: bold;
    border: 2px solid #1e7e34;
    border-radius: 6px;
    padding: 10px 24px;
    width: 100%;
    text-align: center;
    box-shadow: none;
    transition: background-color 0.2s ease-in-out;
}

div.botao-login div.stButton > button:first-child:hover {
    background-color: #218838;
    border-color: #1c7430;
}

/* 🧍 Foto de perfil */
.foto-perfil {
    border: 3px solid #1f77b4;
    border-radius: 50%;
    width: 104px;
    height: 104px;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
    object-fit: cover;
    display: block;
    margin-left: auto;
    margin-right: auto;
}
</style>
""", unsafe_allow_html=True)

# ===== FUNÇÕES GERAIS =====
def navegar_para(pagina, dados=None):
    st.session_state.pagina = pagina
    if dados:
        st.session_state.dados_pagina = dados

    if not st.session_state.get("navegando", False):
        st.session_state.navegando = True
        st.query_params.clear()
        st.rerun()
    else:
        st.session_state.navegando = False

def validar_senha_forte(senha):
    return (
        len(senha) >= 8 and
        any(c.isupper() for c in senha) and
        any(c.islower() for c in senha) and
        any(c.isdigit() for c in senha) and
        any(c in "!@#$%^&*()-_=+[{]};:'\",<.>/?\\|" for c in senha)
    )

def login_page():
    st.markdown(
        "<div class='top-bar'><img src='https://files.oaiusercontent.com/file-b29b60e9-4411-498b-9805-9f50ca782cb5.png' height='40px' /></div><div style='height: 100px;'></div>",
        unsafe_allow_html=True
    )

    col1, col2 = st.columns([1.3, 1])

    with col1:
        st.markdown("""
            <h1 style='color: #1f77b4;'>Bem-vindo ao sistema de cobrança</h1>
            <p style='font-size: 18px;'>Plataforma completa para controle de pacotes e cobranças mensais.</p>
            <img src='https://asaas.com/assets/images/login-banner-new.png' width='90%' style='margin-top:40px;'/>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("### Acesso ao Sistema")
        email = st.text_input("Email", placeholder="Digite seu e-mail")
        senha = st.text_input("Senha", type="password", placeholder="Digite sua senha")
        manter_conectado = st.checkbox("🔒 Manter conectado")

        st.markdown('<div class="botao-login">', unsafe_allow_html=True)

        if st.button("Acessar conta", key="btn_acessar_conta"):
            try:
                payload = {
                    "username": email,
                    "password": senha
                }
                resposta = requests.post(f"{API_BASE}/login/", data=payload)

                if resposta.status_code == 200:
                    dados = resposta.json()
                    st.session_state.token = dados["access_token"]
                    st.session_state.usuario_id = dados.get("id")
                    st.session_state.perfil = dados.get("perfil", "admin")
                    st.session_state.nome = dados.get("nome", "Usuário")
                    st.session_state.foto_url = dados.get("foto_url", "")
                    st.session_state.cpf = dados.get("cpf", "")

                    # Se marcou "manter conectado", salva no cookie
                    if manter_conectado:
                        cookies["token"] = dados["access_token"]
                        cookies["perfil"] = st.session_state.perfil
                        cookies["nome"] = st.session_state.nome
                        cookies["foto_url"] = st.session_state.foto_url
                        cookies["cpf"] = dados.get("cpf", "")
                        cookies.save()

                    # ✅ Redirecionamento obrigatório para troca de senha se ainda estiver com a senha padrão
                    if dados.get("senha_padrao"):
                        st.session_state.pagina = "definir_senha"
                    else:
                        st.session_state.pagina = "menu"


                    st.rerun()

                elif resposta.status_code == 401:
                    st.error("❌ E-mail ou senha incorretos.")
                elif resposta.status_code == 403:
                    st.error("❌ Usuário desativado. Entre em contato com o administrador.")
                else:
                    st.error(f"❌ Erro inesperado: {resposta.status_code} - {resposta.text}")

            except Exception as e:
                st.error(f"❌ Erro ao conectar com a API: {e}")

        st.markdown('</div>', unsafe_allow_html=True)

def input_mascarado(id_html, mascara, label=""):
    html = f"""
    <label for="{id_html}" style="font-weight:600;">{label}</label><br>
    <input id="{id_html}" placeholder="{mascara}" style="width: 100%; padding: 8px; font-size: 16px;" />
    <script src="https://unpkg.com/imask"></script>
    <script>
        const input = document.getElementById("{id_html}");
        if (input) {{
            const mask = IMask(input, {{ mask: '{mascara}' }});
            input.addEventListener('input', () => {{
                window.parent.postMessage({{
                    isStreamlitMessage: true,
                    type: 'streamlit:setComponentValue',
                    value: input.value
                }}, '*');
            }});
        }}
    </script>
    """
    return components.html(html, height=80, key=id_html)

# ===== ROTEADOR GLOBAL UNIFICADO =====
def carregar_pagina():
    pagina = st.session_state.get("pagina", "login")

    # BLOQUEIO DE PRIMEIRO ACESSO - só renderiza tela de senha
    if pagina == "definir_senha":
        tela_definir_senha()
        return

    # Se não estiver logado
    if "token" not in st.session_state:
        if cookies.get("token"):
            st.session_state.token = cookies["token"]
            st.session_state.perfil = cookies.get("perfil", "admin")
            st.session_state.nome = cookies.get("nome", "Usuário")
            st.session_state.foto_url = cookies.get("foto_url", "")
            st.session_state.usuario_id = cookies.get("usuario_id", "default")
            st.session_state.cpf = cookies.get("cpf", "")

            if "pagina" not in st.session_state:
                st.session_state.pagina = query_params.get("pagina", "Início")

            st.query_params.clear()
            st.rerun()
        else:
            login_page()
        return

    # Se for logout
    if st.session_state.get("logout"):
        for chave in ["token", "perfil", "nome", "pagina", "foto_url", "logout"]:
            cookies[chave] = ""
            if chave in st.session_state:
                del st.session_state[chave]
        cookies.save()
        try:
            st.query_params.clear()
        except:
            pass
        st.rerun()
        return

    # Se for qualquer outra página válida
    menu_lateral()

    if pagina == "novo_cliente":
        tela_novo_cliente()
    elif pagina == "consultar_cliente":
        tela_consultar_cliente()
    elif pagina == "meus_dados":
        tela_meus_dados()
    elif pagina == "novo_usuario":
        tela_novo_usuario()
    elif pagina == "lista_usuarios":
        tela_lista_usuarios()
    elif pagina == "editar_usuario":
        from telas.editar_usuario import tela_editar_usuario
        tela_editar_usuario(st.session_state.usuario_id_edicao)
    elif st.session_state.pagina == "detalhes_cliente":
        tela_detalhes_cliente()
        
    elif pagina == "orcamento_pre_pago":
        tela_orcamento_pre_pago()

    elif pagina == "consultar_orcamento":
        consultar_orcamento.consultar_orcamento()

    elif st.session_state.pagina == "fluxo_reserva":
        from telas import fluxo_reserva
        fluxo_reserva.fluxo_reserva()

    elif pagina == "empresa":
        tela_empresa()
    
    elif pagina == "consultar_pacotes":
        tela_consultar_pacotes()


    
# ✅ FLUXO FINAL
carregar_pagina()
