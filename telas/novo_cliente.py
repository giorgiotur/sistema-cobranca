import streamlit as st
import requests
import re
import time

from utils.formatters import formatar_cpf, formatar_telefone, formatar_cep
from utils.validators import validar_cpf, validar_telefone, validar_email, validar_cep
from utils.endereco import buscar_cep
from datetime import date

API_BASE = "http://127.0.0.1:8000"

def tela_novo_cliente():
    st.title("📝 Cadastro de Novo Cliente")

    # ✅ Espaçamento extra
    st.markdown("<div style='margin-top: 60px;'></div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    cpf_duplicado = False
    email_duplicado = False

    with col1:
        nome_completo = st.text_input("👤 Nome completo *", key="nome_completo")

        cpf = st.text_input("🆔 CPF *", key="cpf")
        if cpf:
            st.markdown(f"🧾 `{formatar_cpf(cpf)}`")
            if len(re.sub(r'\D', '', cpf)) == 11:
                try:
                    resposta = requests.get(f"{API_BASE}/clientes/verificar/", params={"cpf": re.sub(r'\D', '', cpf)})
                    if resposta.status_code == 200 and resposta.json().get("cpf"):
                        st.warning("⚠️ Este CPF já está cadastrado no sistema.")
                        cpf_duplicado = True
                except Exception as e:
                    st.error("Erro ao verificar CPF.")

        telefone = st.text_input("📞 Telefone *", key="telefone")
        if telefone:
            st.markdown(f"📞 `{formatar_telefone(telefone)}`")
        
        # ✅ NOVO CAMPO: Data de Nascimento
        data_nascimento = st.date_input(
            "📅 Data de Nascimento",
            value=date.today(),
            min_value=date(1900, 1, 1),
            max_value=date.today(),
            key="data_nascimento",
            format="DD/MM/YYYY"
        )

        email = st.text_input("✉️ E-mail *", key="email")
        if email and "@" in email:
            try:
                resposta = requests.get(f"{API_BASE}/clientes/verificar/", params={"email": email})
                if resposta.status_code == 200 and resposta.json().get("email"):
                    st.warning("⚠️ Este e-mail já está cadastrado no sistema.")
                    email_duplicado = True
            except Exception as e:
                st.error("Erro ao verificar e-mail.")

        cep = st.text_input("📍 CEP *", key="cep")
        if cep:
            st.markdown(f"📍 `{formatar_cep(cep)}`")

            cep_limpo = re.sub(r'\D', '', cep)
            cep_ja_consultado = st.session_state.get("cep_consultado_valor", "")

            if validar_cep(cep) and cep_limpo != cep_ja_consultado:
                with st.spinner("🔄 Buscando endereço, por favor aguarde..."):
                    dados_cep = buscar_cep(cep)
                    time.sleep(1)

                if dados_cep and not dados_cep.get("erro"):
                    st.session_state["rua"] = dados_cep.get("logradouro", "")
                    st.session_state["bairro"] = dados_cep.get("bairro", "")
                    st.session_state["cidade"] = dados_cep.get("localidade", "")
                    st.session_state["estado"] = dados_cep.get("uf", "")
                    st.session_state["cep_consultado_valor"] = cep_limpo
                else:
                    st.error("❌ Erro ao consultar o CEP.")

    with col2:
        rua = st.text_input("🏠 Rua *", key="rua")
        bairro = st.text_input("🏘️ Bairro *", key="bairro")
        cidade = st.text_input("🌆 Cidade *", key="cidade")
        estado = st.text_input("🗺️ Estado *", key="estado")
        numero = st.text_input("🔢 Número *", key="numero")
        complemento = st.text_input("➕ Complemento (opcional)", key="complemento")

    col_esq, col_btn, col_dir = st.columns([3, 2, 3])
    with col_btn:
        if st.button("💾 Cadastrar Cliente"):
            erros = []

            campos_obrigatorios = {
                "Nome completo": nome_completo,
                "CPF": cpf,
                "Telefone": telefone,
                "E-mail": email,
                "CEP": cep,
                "Rua": rua,
                "Bairro": bairro,
                "Cidade": cidade,
                "Estado": estado,
                "Número": numero,
            }

            for campo, valor in campos_obrigatorios.items():
                if not valor.strip():
                    erros.append(f"⚠️ O campo **{campo}** é obrigatório.")

            if cpf and not validar_cpf(cpf):
                erros.append("CPF inválido (deve conter 11 dígitos).")
            if telefone and not validar_telefone(telefone):
                erros.append("Telefone inválido (deve conter 10 ou 11 dígitos).")
            if cep and not validar_cep(cep):
                erros.append("CEP inválido (deve conter 8 dígitos).")
            if email and not validar_email(email):
                erros.append("E-mail inválido.")
            if cpf_duplicado:
                erros.append("CPF já está cadastrado no sistema.")
            if email_duplicado:
                erros.append("E-mail já está cadastrado no sistema.")

            if erros:
                st.error("❌ Corrija os erros abaixo antes de enviar:")
                for erro in erros:
                    st.markdown(f"- {erro}")
            else:
                payload = {
                    "nome": nome_completo.strip(),
                    "telefone": formatar_telefone(telefone),
                    "email": email.strip(),
                    "cpf": formatar_cpf(cpf),
                    "cep": formatar_cep(cep),
                    "rua": rua.strip(),
                    "numero": numero.strip(),
                    "complemento": complemento.strip(),
                    "bairro": bairro.strip(),
                    "cidade": cidade.strip(),
                    "estado": estado.strip(),
                    "data_nascimento": data_nascimento.isoformat() if data_nascimento else None,
                }

                try:
                    resposta = requests.post(f"{API_BASE}/clientes/", json=payload)
                    if resposta.status_code == 200:
                        st.success("✅ Cliente cadastrado com sucesso!")

                        # Limpar campos
                        for key in list(payload.keys()) + ["cep_consultado_valor", "nome_completo", "cpf", "telefone", "email"]:
                            if key in st.session_state:
                                del st.session_state[key]

                        time.sleep(2)
                        st.rerun()

                    else:
                        st.error(f"❌ Erro: {resposta.status_code} - {resposta.text}")

                except Exception as e:
                    st.error(f"❌ Erro ao conectar com a API: {str(e)}")
