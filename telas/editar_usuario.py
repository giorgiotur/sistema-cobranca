import streamlit as st
import requests
from config import API_BASE
from utils.endereco import buscar_cep  # ✅ Função de consulta de CEP ViaCEP
from datetime import datetime, date


def tela_editar_usuario(usuario_id: int):
    st.markdown("## ✏️ Editar Usuário")

    resposta = requests.get(f"{API_BASE}/usuarios/{usuario_id}", headers={"Authorization": f"Bearer {st.session_state.token}"})
    if resposta.status_code != 200:
        st.error("Erro ao carregar os dados do usuário.")
        return

    usuario = resposta.json()
    perfil_logado = st.session_state.perfil.lower()

    # ✅ Bloqueio total para clientes
    if perfil_logado == "cliente":
        st.error("❌ Você não tem permissão para acessar esta área.")
        st.stop()

    # ✅ Bloqueio para agente: só pode editar clientes
    if perfil_logado == "agente" and usuario.get("perfil") != "cliente":
        st.error("❌ Você não tem permissão para editar este tipo de usuário.")
        if st.button("🔙 Voltar para Lista de Usuários"):
            st.session_state.pagina = "lista_usuarios"
            st.rerun()
        st.stop()

    nome = st.text_input("Nome completo", value=usuario["nome"])

    if perfil_logado == "admin":
        email = st.text_input("E-mail", value=usuario["email"])
        cpf = st.text_input("CPF", value=usuario.get("cpf", ""))
    else:
        st.markdown(f"**E-mail:** {usuario['email']}")
        email = usuario["email"]
        st.markdown(f"**CPF:** {usuario.get('cpf', '—')}")
        cpf = usuario.get("cpf", "")
    
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

    # ===== Função para consulta automática de CEP =====
    def consultar_cep_auto():
        cep_valor = st.session_state.get("cep_input", "")
        if cep_valor:
            st.info("🔄 Consultando endereço, aguarde...")
            endereco = buscar_cep(cep_valor)
            if endereco and "erro" not in endereco:
                st.session_state["rua_input"] = endereco.get("logradouro", "")
                st.session_state["bairro_input"] = endereco.get("bairro", "")
                st.session_state["cidade_input"] = endereco.get("localidade", "")
                st.session_state["estado_input"] = endereco.get("uf", "")
                st.success("✅ Endereço carregado com sucesso!")
            else:
                st.error("❌ CEP não encontrado. Verifique o número digitado.")

    # ===== Endereço e telefone =====
    st.info("🔔 Ao preencher o campo CEP e sair do campo, o sistema irá buscar automaticamente o endereço para você.")

    cep = st.text_input("CEP", value=usuario.get("cep", ""), key="cep_input", on_change=consultar_cep_auto)
    rua = st.text_input("Rua", value=usuario.get("rua", ""), key="rua_input")
    numero = st.text_input("Número", value=usuario.get("numero", ""))
    complemento = st.text_input("Complemento", value=usuario.get("complemento", ""), key="complemento_input")
    bairro = st.text_input("Bairro", value=usuario.get("bairro", ""), key="bairro_input")
    cidade = st.text_input("Cidade", value=usuario.get("cidade", ""), key="cidade_input")
    estado = st.text_input("Estado", value=usuario.get("estado", ""), key="estado_input")
    telefone = st.text_input("Telefone", value=usuario.get("telefone", ""))

    

    # ===== Perfil =====
    perfis_disponiveis = ["admin", "agente", "cliente"] if perfil_logado == "admin" else ["cliente"]
    perfil_atual = usuario.get("perfil", "cliente")
    if perfil_atual in perfis_disponiveis:
        index_atual = perfis_disponiveis.index(perfil_atual)
    else:
        index_atual = 0

    perfil_selecionado = st.selectbox("Perfil de acesso", options=perfis_disponiveis, index=index_atual)
    perfil_to_role_id = {"admin": 1, "agente": 2, "cliente": 3}
    role_id = perfil_to_role_id.get(perfil_selecionado, 3)

    # ===== Botões =====
    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("💾 Salvar alterações", use_container_width=True):
            payload = {
                "nome": nome,
                "email": email,
                "cpf": cpf,
                "role_id": role_id,
                "cep": cep,
                "rua": rua,
                "numero": numero,
                "complemento": complemento,
                "bairro": bairro,
                "cidade": cidade,
                "estado": estado,
                "telefone": telefone,
                "data_nascimento": data_nascimento.isoformat() if data_nascimento else None
            }
            try:
                resposta_salvar = requests.put(
                    f"{API_BASE}/usuarios/{usuario_id}",
                    json=payload,
                    headers={"Authorization": f"Bearer {st.session_state.token}"}
                )
                if resposta_salvar.status_code == 200:
                    st.success("✅ Usuário atualizado com sucesso!")
                    st.session_state.pagina = "lista_usuarios"
                    st.rerun()
                elif resposta_salvar.status_code == 401:
                    st.error("❌ Token inválido ou sessão expirada. Faça login novamente.")
                else:
                    erro = resposta_salvar.json().get("detail", "Erro ao atualizar usuário.")
                    st.error(f"❌ {erro}")
            except Exception as e:
                st.error(f"❌ Erro ao conectar com a API: {e}")

    with col2:
        if st.button("🔙 Voltar", use_container_width=True):
            st.session_state.pagina = "lista_usuarios"
            st.rerun()
            
    