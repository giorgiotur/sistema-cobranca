import os
from dotenv import load_dotenv
import streamlit as st
import requests

# ✅ Carrega variáveis do .env
load_dotenv()
API_BASE = os.getenv("API_BASE")

def tela_novo_usuario():
    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
    st.markdown("## ➕ Novo Usuário")

    # ===== Espaço extra abaixo do título =====
    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

    # ===== Input de Busca Centralizado =====
    col_c1, col_input, col_c2 = st.columns([3, 4, 3])
    with col_input:
        busca = st.text_input("🔎 Buscar cliente por CPF ou E-mail", key="buscar_novo_usuario")

    # ✅ Limpa cliente automaticamente se o campo de busca estiver vazio
    if busca.strip() == "" and "cliente_selecionado" in st.session_state:
        del st.session_state.cliente_selecionado

    # ===== Botões: Buscar Cliente e Voltar =====
    col_b1, col_b2, col_b3, col_b4, col_b5 = st.columns([2, 2, 1, 2, 2])

    with col_b2:
        if st.button("🔍 Buscar Cliente", use_container_width=True):
            try:
                resposta = requests.get(
                    f"{API_BASE}/clientes/por-cpf-ou-email-ou-nome/{busca}",
                    headers={"Authorization": f"Bearer {st.session_state.token}"}
                )

                if resposta.status_code == 200:
                    cliente = resposta.json()
                    st.session_state.cliente_selecionado = cliente
                    st.success("✅ Cliente encontrado!")

                elif resposta.status_code == 400:
                    detalhe = resposta.json().get("detail", "Cliente já possui acesso ao sistema como usuário.")
                    st.warning(f"⚠️ {detalhe}")

                elif resposta.status_code == 404:
                    st.error("❌ Cliente não encontrado.")

                else:
                    st.error(f"❌ Erro inesperado: {resposta.status_code} - {resposta.text}")

            except Exception as e:
                st.error(f"❌ Erro na requisição: {e}")

    with col_b4:
        if st.button("🔙 Voltar", use_container_width=True):
            if "cliente_selecionado" in st.session_state:
                del st.session_state.cliente_selecionado
            if "buscar_novo_usuario" in st.session_state:
                del st.session_state.buscar_novo_usuario
            st.session_state.pagina = "lista_usuarios"
            st.rerun()

    # ===== Se houver cliente carregado na sessão =====
    if "cliente_selecionado" in st.session_state:
        cliente = st.session_state.cliente_selecionado

        # ✅ Se o cliente já for usuário (já tiver role_id), mostrar aviso e não exibir formulário
        if cliente.get("role_id"):
            st.warning(f"⚠️ Este cliente já possui acesso ao sistema como usuário.")
        else:
            # ✅ Formulário de Criação de Novo Usuário
            st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)
            st.markdown("### ✏️ Dados do Novo Usuário")

            nome = st.text_input("Nome", value=cliente.get("nome", ""))
            cpf = st.text_input("CPF", value=cliente.get("cpf", ""))
            email = st.text_input("E-mail", value=cliente.get("email", ""))

            # ✅ Perfil disponível conforme perfil do usuário logado
            perfil_logado = st.session_state.perfil.lower()
            perfis_disponiveis = []

            if perfil_logado == "admin":
                perfis_disponiveis = ["admin", "agente", "cliente"]
            elif perfil_logado == "agente":
                perfis_disponiveis = ["cliente"]

            perfil = st.selectbox("Perfil do Usuário", perfis_disponiveis)

            st.info("📌 O usuário será criado como **inativo**, com a senha padrão **123456**.\n\nEle só poderá acessar o sistema após alterar a senha no primeiro login.")

            col1, col2 = st.columns(2)

            with col1:
                if st.button("✅ Criar Usuário"):
                    # ✅ Mapeia perfil para role_id
                    perfil_role_map = {"admin": 1, "agente": 2, "cliente": 3}
                    role_id = perfil_role_map.get(perfil)

                    # ✅ Validação de campos obrigatórios
                    if not nome or not cpf or not email or not role_id:
                        st.error("❌ Preencha todos os campos obrigatórios.")
                    else:
                        payload = {
                            "nome": nome,
                            "cpf": cpf,
                            "email": email,
                            "role_id": role_id
                        }

                        try:
                            resposta = requests.post(
                                f"{API_BASE}/usuarios/",
                                json=payload,
                                headers={"Authorization": f"Bearer {st.session_state.token}"}
                            )

                            if resposta.status_code == 200:
                                data = resposta.json()

                                # ✅ Salva info para exibir mensagem na próxima tela
                                st.session_state.usuario_criado = {
                                    "nome": data.get("nome"),
                                    "email": data.get("email"),
                                    "senha": "123456"
                                }

                                # ✅ Limpa estado de cliente buscado e volta para a lista
                                if "cliente_selecionado" in st.session_state:
                                    del st.session_state.cliente_selecionado
                                if "buscar_novo_usuario" in st.session_state:
                                    del st.session_state.buscar_novo_usuario

                                st.session_state.pagina = "lista_usuarios"
                                st.rerun()

                            else:
                                st.error(f"❌ Erro ao criar usuário: {resposta.text}")

                        except Exception as e:
                            st.error(f"❌ Erro na requisição: {e}")

            with col2:
                if st.button("❌ Cancelar"):
                    if "cliente_selecionado" in st.session_state:
                        del st.session_state.cliente_selecionado
                    if "buscar_novo_usuario" in st.session_state:
                        del st.session_state.buscar_novo_usuario
                    st.session_state.pagina = "lista_usuarios"
                    st.rerun()

# ✅ Placeholder para evitar erro de import
def tela_novo_cliente():
    st.title("Tela Novo Cliente - Em breve disponível")
