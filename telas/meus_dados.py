import streamlit as st
import requests
from dotenv import load_dotenv
import os
from utils.endereco import buscar_cep
from datetime import datetime, date

load_dotenv()
API_BASE = os.getenv("API_BASE", "http://localhost:8000")

def tela_meus_dados():
    usuario_id = st.session_state.get("usuario_id")
    if not usuario_id:
        st.error("❌ Usuário não autenticado.")
        return

    perfil_logado = st.session_state.perfil.lower()
    #st.subheader("🧪 DEBUG")
    #st.write("ID do usuário:", usuario_id)
    #st.write("Token:", st.session_state.get("token"))
    #st.write("API_BASE:", API_BASE)

    try:
        resposta = requests.get(
            f"{API_BASE}/usuarios/{usuario_id}",
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )
        if resposta.status_code != 200:
            st.error(f"❌ Erro ao carregar os dados do usuário. Código {resposta.status_code}: {resposta.text}")

            return
        usuario = resposta.json()
    except Exception as e:
        st.error(f"❌ Erro ao conectar com a API: {e}")
        return

    if "modo_edicao" not in st.session_state:
        st.session_state.modo_edicao = False
    if "cep_mensagem" not in st.session_state:
        st.session_state.cep_mensagem = ""

    def consultar_cep_auto():
        cep_valor = st.session_state.get("cep_input", "").strip()

        # Limpa os campos de endereço antes
        st.session_state["rua_input"] = ""
        st.session_state["bairro_input"] = ""
        st.session_state["cidade_input"] = ""
        st.session_state["estado_input"] = ""
        st.session_state.cep_mensagem = ""

        if cep_valor:
            endereco = buscar_cep(cep_valor)
            if endereco and "erro" not in endereco:
                st.session_state["rua_input"] = endereco.get("logradouro", "")
                st.session_state["bairro_input"] = endereco.get("bairro", "")
                st.session_state["cidade_input"] = endereco.get("localidade", "")
                st.session_state["estado_input"] = endereco.get("uf", "")
                st.session_state.cep_mensagem = "✅ Endereço preenchido com sucesso."
            else:
                st.session_state.cep_mensagem = "❌ CEP não encontrado. Por favor, verifique o valor digitado."

    if not st.session_state.modo_edicao:
        st.title("👤 Meus Dados")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"**👤 Nome completo:** {usuario.get('nome', '—')}")
            st.markdown(f"**🆔 CPF:** {usuario.get('cpf', '—')}")
            st.markdown(f"**📅 Data de Nascimento:** {usuario.get('data_nascimento', '—')}")
            st.markdown(f"**📞 Telefone:** {usuario.get('telefone', '—')}")
            st.markdown(f"**✉️ E-mail:** {usuario.get('email', '—')}")
            st.markdown(f"**📍 CEP:** {usuario.get('cep', '—')}")

        with col2:
            st.markdown(f"**🏠 Rua:** {usuario.get('rua', '—')}")
            st.markdown(f"**🏘️ Bairro:** {usuario.get('bairro', '—')}")
            st.markdown(f"**🌆 Cidade:** {usuario.get('cidade', '—')}")
            st.markdown(f"**🗺️ Estado:** {usuario.get('estado', '—')}")
            st.markdown(f"**🔢 Número:** {usuario.get('numero', '—')}")
            st.markdown(f"**➕ Complemento:** {usuario.get('complemento', '—')}")

        if st.button("✏️ Editar Meus Dados", use_container_width=True):
            st.session_state.modo_edicao = True
            st.rerun()

    else:
        st.title("✏️ Editar Meus Dados")

        col1, col2 = st.columns(2)

        with col1:
            nome = st.text_input("👤 Nome completo", value=usuario.get("nome", ""))

            if perfil_logado == "admin":
                cpf = st.text_input("🆔 CPF", value=usuario.get("cpf", ""))
                email = st.text_input("✉️ E-mail", value=usuario.get("email", ""))
            else:
                cpf = usuario.get("cpf", "")
                email = usuario.get("email", "")

            telefone = st.text_input("📞 Telefone", value=usuario.get("telefone", ""))

            # ✅ NOVO CAMPO: Data de Nascimento
            data_nascimento_valor = usuario.get("data_nascimento")
            data_nascimento_convertida = (
                datetime.strptime(data_nascimento_valor, "%Y-%m-%d").date()
                if data_nascimento_valor else date.today()
            )

            data_nascimento = st.date_input(
                "📅 Data de Nascimento",
                value=data_nascimento_convertida,
                min_value=date(1900, 1, 1),
                max_value=date.today()
            )

            def cep_on_change():
                consultar_cep_auto()

            cep = st.text_input("📍 CEP", value=usuario.get("cep", ""), key="cep_input", on_change=cep_on_change)

            # Mensagem fixa de CEP
            if st.session_state.get("cep_mensagem", ""):
                st.markdown(f"{st.session_state.cep_mensagem}")

        with col2:
            rua = st.text_input("🏠 Rua", value=usuario.get("rua", ""), key="rua_input")
            numero = st.text_input("🔢 Número", value=usuario.get("numero", ""))
            complemento = st.text_input("➕ Complemento", value=usuario.get("complemento", ""), key="complemento_input")
            bairro = st.text_input("🏘️ Bairro", value=usuario.get("bairro", ""), key="bairro_input")
            cidade = st.text_input("🌆 Cidade", value=usuario.get("cidade", ""), key="cidade_input")
            estado = st.text_input("🗺️ Estado", value=usuario.get("estado", ""), key="estado_input")

        col_salvar, col_cancelar = st.columns(2)

        with col_salvar:
            if st.button("💾 Salvar alterações", use_container_width=True):
                campos_obrigatorios = {
                    "nome": nome,
                    "telefone": telefone,
                    "cep": st.session_state.get("cep_input", ""),
                    "rua": st.session_state.get("rua_input", ""),
                    "numero": numero,
                    "bairro": st.session_state.get("bairro_input", ""),
                    "cidade": st.session_state.get("cidade_input", ""),
                    "estado": st.session_state.get("estado_input", "")
                }

                if perfil_logado == "admin":
                    campos_obrigatorios["cpf"] = cpf
                    campos_obrigatorios["email"] = email

                faltando = [campo for campo, valor in campos_obrigatorios.items() if not valor.strip()]

                if faltando:
                    campos_formatados = ", ".join(faltando)
                    st.warning(f"⚠️ Preencha os campos obrigatórios: {campos_formatados}")
                else:
                    payload = {
                        "nome": nome,
                        "cpf": cpf,
                        "email": email,
                        "telefone": telefone,
                        "cep": st.session_state.get("cep_input", usuario.get("cep", "")),
                        "rua": st.session_state.get("rua_input", usuario.get("rua", "")),
                        "numero": numero,
                        "complemento": st.session_state.get("complemento_input", usuario.get("complemento", "")),
                        "bairro": st.session_state.get("bairro_input", usuario.get("bairro", "")),
                        "cidade": st.session_state.get("cidade_input", usuario.get("cidade", "")),
                        "estado": st.session_state.get("estado_input", usuario.get("estado", "")),
                        "data_nascimento": data_nascimento.isoformat() if data_nascimento else None
                    }

                    if perfil_logado == "agente":
                        payload.pop("cpf")
                        payload.pop("email")

                    try:
                        resposta = requests.put(
                            f"{API_BASE}/usuarios/{usuario_id}",
                            json=payload,
                            headers={"Authorization": f"Bearer {st.session_state.token}"}
                        )

                        if resposta.status_code == 200:
                            st.success("✅ Dados atualizados com sucesso!")
                            st.session_state.modo_edicao = False
                            st.rerun()
                        else:
                            st.error(f"❌ Erro ao salvar: {resposta.text}")
                    except Exception as e:
                        st.error(f"❌ Erro ao conectar com a API: {e}")

        with col_cancelar:
            if st.button("❌ Cancelar", use_container_width=True):
                st.session_state.modo_edicao = False
                st.rerun()
