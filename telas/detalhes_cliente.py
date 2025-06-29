import streamlit as st
import requests
from dotenv import load_dotenv
import os
from utils.endereco import buscar_cep
from datetime import datetime, date

load_dotenv()
API_BASE = os.getenv("API_BASE", "http://localhost:8000")

def tela_detalhes_cliente():
    cliente_id = st.session_state.get("cliente_id")
    if not cliente_id:
        st.error("❌ Nenhum cliente selecionado.")
        return

    perfil_logado = st.session_state.perfil.lower()

    if perfil_logado == "cliente":
        st.error("❌ Você não tem permissão para acessar esta área.")
        return

    try:
        resposta = requests.get(
            f"{API_BASE}/clientes/{cliente_id}",
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )
        if resposta.status_code != 200:
            st.error("❌ Erro ao carregar os dados do cliente.")
            return
        cliente = resposta.json()
    except Exception as e:
        st.error(f"❌ Erro ao conectar com a API: {e}")
        return

    if "modo_edicao" not in st.session_state:
        st.session_state.modo_edicao = False
    if "cep_mensagem" not in st.session_state:
        st.session_state.cep_mensagem = ""

    def consultar_cep_auto():
        cep_valor = st.session_state.get("cep_input", "").strip()

        # Limpar campos antes de buscar
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
        st.title("👤 Detalhes do Cliente")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"**👤 Nome completo:** {cliente.get('nome', '—')}")
            st.markdown(f"**🆔 CPF:** {cliente.get('cpf', '—')}")
            st.markdown(f"**📅 Data de Nascimento:** {cliente.get('data_nascimento', '—')}")
            st.markdown(f"**📞 Telefone:** {cliente.get('telefone', '—')}")
            st.markdown(f"**✉️ E-mail:** {cliente.get('email', '—')}")
            st.markdown(f"**📍 CEP:** {cliente.get('cep', '—')}")

            status_asaas = cliente.get('asaas_status', '—')
            if status_asaas and status_asaas.lower() == "sucesso":
                st.info(f"📊 Status Asaas: {status_asaas}")
            else:
                st.error(f"📊 Status Asaas: {status_asaas or '❌ Não processado'}")

        with col2:
            st.markdown(f"**🏠 Rua:** {cliente.get('rua', '—')}")
            st.markdown(f"**🏘️ Bairro:** {cliente.get('bairro', '—')}")
            st.markdown(f"**🌆 Cidade:** {cliente.get('cidade', '—')}")
            st.markdown(f"**🗺️ Estado:** {cliente.get('estado', '—')}")
            st.markdown(f"**🔢 Número:** {cliente.get('numero', '—')}")
            st.markdown(f"**➕ Complemento:** {cliente.get('complemento', '—')}")

        col_editar, col_voltar = st.columns(2)

        with col_editar:
            if perfil_logado in ["admin", "agente"]:
                if st.button("✏️ Editar Cliente", use_container_width=True):
                    st.session_state.modo_edicao = True
                    st.rerun()

        with col_voltar:
            if st.button("🔙 Voltar", use_container_width=True):
                st.session_state.busca_cliente = cliente.get("cpf", "")
                if "resultado_clientes" in st.session_state:
                    del st.session_state.resultado_clientes
                st.session_state.pagina = "consultar_cliente"
                st.rerun()

    else:
        st.title("✏️ Editar Cliente")

        col1, col2 = st.columns(2)

        with col1:
            nome = st.text_input("👤 Nome completo", value=cliente.get("nome", ""))

            if perfil_logado == "admin":
                cpf = st.text_input("🆔 CPF", value=cliente.get("cpf", ""))
                email = st.text_input("✉️ E-mail", value=cliente.get("email", ""))
            else:
                cpf = cliente.get("cpf", "")
                email = cliente.get("email", "")

            telefone = st.text_input("📞 Telefone", value=cliente.get("telefone", ""))

            # ✅ NOVO CAMPO: Data de Nascimento
            data_nascimento_valor = cliente.get("data_nascimento")
            data_nascimento_convertida = (
                datetime.strptime(data_nascimento_valor, "%Y-%m-%d").date()
                if data_nascimento_valor else None
            )

            data_nascimento = st.date_input(
                "📅 Data de Nascimento",
                value=data_nascimento_convertida if data_nascimento_convertida else date.today(),
                min_value=date(1900, 1, 1),
                max_value=date.today()
            )

            def cep_on_change():
                consultar_cep_auto()

            cep = st.text_input("📍 CEP", value=cliente.get("cep", ""), key="cep_input", on_change=cep_on_change)

            # Mensagem de status do CEP
            if st.session_state.get("cep_mensagem", ""):
                st.markdown(f"{st.session_state.cep_mensagem}")

        with col2:
            rua = st.text_input("🏠 Rua", value=cliente.get("rua", ""), key="rua_input")
            numero = st.text_input("🔢 Número", value=cliente.get("numero", ""))
            complemento = st.text_input("➕ Complemento", value=cliente.get("complemento", ""), key="complemento_input")
            bairro = st.text_input("🏘️ Bairro", value=cliente.get("bairro", ""), key="bairro_input")
            cidade = st.text_input("🌆 Cidade", value=cliente.get("cidade", ""), key="cidade_input")
            estado = st.text_input("🗺️ Estado", value=cliente.get("estado", ""), key="estado_input")

        col_salvar, col_cancelar = st.columns(2)

        with col_salvar:
            if st.button("💾 Salvar alterações", use_container_width=True):
                campos_obrigatorios = {
                    "nome": nome,
                    "telefone": telefone,
                    "data_nascimento": st.session_state.get("data_nascimento_input",data_nascimento.isoformat() if data_nascimento else ""),
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
                        "cep": st.session_state.get("cep_input", cliente.get("cep", "")),
                        "rua": st.session_state.get("rua_input", cliente.get("rua", "")),
                        "numero": numero,
                        "complemento": st.session_state.get("complemento_input", cliente.get("complemento", "")),
                        "bairro": st.session_state.get("bairro_input", cliente.get("bairro", "")),
                        "cidade": st.session_state.get("cidade_input", cliente.get("cidade", "")),
                        "estado": st.session_state.get("estado_input", cliente.get("estado", "")),
                        "data_nascimento": data_nascimento.isoformat() if data_nascimento else None
                    }

                    if perfil_logado == "agente":
                        payload.pop("cpf")
                        payload.pop("email")

                    try:
                        resposta = requests.put(
                            f"{API_BASE}/clientes/{cliente_id}",
                            json=payload,
                            headers={"Authorization": f"Bearer {st.session_state.token}"}
                        )

                        if resposta.status_code == 200:
                            st.success("✅ Cliente atualizado com sucesso!")
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
