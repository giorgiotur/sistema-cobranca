import streamlit as st
import requests
from utils.endereco import buscar_cep
from utils.token import BASE_URL_API, carregar_token
import os
from dotenv import load_dotenv
load_dotenv()
BASE_URL_API = os.getenv("API_BASE")

def tela_empresa():
    st.title("🏢 Cadastro da Empresa")

    token = carregar_token()
    if not token:
        st.warning("Você precisa estar logado para acessar esta página.")
        return

    headers = {"Authorization": f"Bearer {token}"}
    url_busca = f"{BASE_URL_API}/empresas/"

    # Inicializar session_state
    if "cep_digitado" not in st.session_state:
        st.session_state.cep_digitado = ""
    if "endereco_empresa" not in st.session_state:
        st.session_state.endereco_empresa = {}

    dados_empresa = {}
    try:
        resposta = requests.get(url_busca, headers=headers)
        if resposta.status_code == 200:
            dados_empresa = resposta.json()
        else:
            st.info("Nenhuma empresa cadastrada ainda.")
    except Exception as e:
        st.error(f"Erro ao buscar dados da empresa: {e}")
        return

    with st.form("form_empresa"):
        st.subheader("📋 Dados da Empresa")

        razao_social = st.text_input("Razão Social", value=dados_empresa.get("razao_social", ""))
        nome_fantasia = st.text_input("Nome Fantasia", value=dados_empresa.get("nome_fantasia", ""))
        cnpj = st.text_input("CNPJ", value=dados_empresa.get("cnpj", ""))
        cep_input = st.text_input("CEP", value=dados_empresa.get("cep", ""))

        # Detectar mudança no CEP
        if cep_input != st.session_state.cep_digitado and len(cep_input) == 8:
            st.session_state.cep_digitado = cep_input
            endereco = buscar_cep(cep_input)
            if endereco:
                st.session_state.endereco_empresa = endereco
                st.experimental_rerun()

        endereco = st.session_state.get("endereco_empresa", {})

        rua = st.text_input("Rua", value=dados_empresa.get("logradouro", endereco.get("logradouro", "")))
        numero = st.text_input("Número", value=dados_empresa.get("numero", ""))
        bairro = st.text_input("Bairro", value=dados_empresa.get("bairro", endereco.get("bairro", "")))
        municipio = st.text_input("Município", value=dados_empresa.get("municipio", endereco.get("localidade", "")))
        uf = st.text_input("UF", value=dados_empresa.get("uf", ""))
        telefone = st.text_input("Telefone", value=dados_empresa.get("telefone", ""))

        submit = st.form_submit_button("💾 Salvar")

        if submit:
            payload = {
                "razao_social": razao_social,
                "nome_fantasia": nome_fantasia,
                "cnpj": cnpj,
                "cep": cep_input,
                "logradouro": rua,
                "numero": numero,
                "bairro": bairro,
                "municipio": municipio,
                "uf": uf,  
                "telefone": telefone,
            }

            try:
                if dados_empresa:
                    resposta = requests.put(url_busca, json=payload, headers=headers)
                else:
                    resposta = requests.post(url_busca, json=payload, headers=headers)

                if resposta.status_code == 201:
                    st.success("✅ Empresa cadastrada com sucesso.")
                    
                elif resposta.status_code == 200:
                    st.info("🔄 Dados da empresa atualizados com sucesso.")
                    
                else:
                    st.error(f"❌ Erro ao salvar: {resposta.text}")

            except Exception as e:
                st.error(f"❌ Erro na requisição: {e}")