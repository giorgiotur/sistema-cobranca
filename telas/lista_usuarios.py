import streamlit as st
import requests
import os
import time
from dotenv import load_dotenv

load_dotenv()
API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")

def tela_lista_usuarios():
    # ✅ Bloqueio para clientes
    if st.session_state.perfil.lower() == "cliente":
        st.error("❌ Você não tem permissão para acessar esta área.")
        st.stop()

    st.title("👥 Lista de Usuários")

    # ==== Cabeçalho da Lista de Usuários ====
    col1, col2 = st.columns([6, 2])

    with col1:
        st.markdown("")

    with col2:
        st.markdown("<div style='text-align: right;'>", unsafe_allow_html=True)
        if st.button("➕ Novo Usuário", key="btn_novo_usuario"):
            st.session_state.pagina = "novo_usuario"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # Depois (opcional): Adicione CSS global para personalizar o botão com mais destaque
    st.markdown("""
        <style>
        div.stButton > button#btn_novo_usuario {
            background-color: var(--secondary-background-color);
            border: 2px solid black;
            border-radius: 8px;
            padding: 8px 16px;
            color: black;
            font-weight: bold;
            cursor: pointer;
        }
        </style>
    """, unsafe_allow_html=True)

    # ===== Filtros =====
    col_f1, col_f2, col_f3 = st.columns([5, 3, 3])

    with col_f1:
        termo_busca = st.text_input("🔎 Buscar por nome, CPF ou e-mail", key="filtro_busca")

    with col_f2:
        filtro_perfil = st.selectbox(
            "Filtrar por perfil",
            options=["Todos", "admin", "agente", "cliente"],
            index=0,
            key="filtro_perfil"
        )

    with col_f3:
        filtro_status = st.selectbox(
            "Filtrar por status",
            options=["Todos", "Ativos", "Inativos"],
            index=0,
            key="filtro_status"
        )


    # ===== Buscar usuários da API =====
    try:
        resposta = requests.get(f"{API_BASE}/usuarios/", headers={"Authorization": f"Bearer {st.session_state.token}"})
        if resposta.status_code == 200:
            usuarios = resposta.json()
        else:
            st.error("Erro ao carregar usuários.")
            return
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return
    
    # ✅ Exibir mensagem de sucesso de novo usuário criado
    if "usuario_criado" in st.session_state:
        novo_usuario = st.session_state.usuario_criado
        st.success(f"✅ Usuário {novo_usuario['nome']} criado com sucesso com senha padrão: 123456")

        texto_whatsapp = f"""
Olá, tudo bem?

*Seu acesso ao sistema Viagem Programada foi criado!*

🔑 Login: {novo_usuario['email']}
🔑 Senha: 123456

👉 Link de acesso: http://localhost:8501

Por segurança, recomendamos que altere a senha no primeiro acesso.
"""

        with st.expander("📲 Visualizar modelo de mensagem para WhatsApp", expanded=True):
            st.code(texto_whatsapp, language="")

        if st.button("❌ Fechar esta mensagem", key="fechar_usuario_criado"):
            del st.session_state.usuario_criado
            st.rerun()

    # ✅ Exibir mensagem de sucesso do último reenvio de senha
    if "reenvio_sucesso" in st.session_state:
        usuario_id_sucesso = st.session_state.reenvio_sucesso
        usuario_sucesso = next((u for u in usuarios if u["id"] == usuario_id_sucesso), None)

        if usuario_sucesso:
            st.success(f"✅ Senha de {usuario_sucesso['nome']} redefinida com sucesso para: **123456**")

            texto_whatsapp = f"""
Olá, tudo bem?

*Sua senha de acesso ao sistema Viagem Programada foi redefinida para:*

🔑 Senha padrão: 123456

Por segurança, ao fazer login, o sistema vai pedir para você criar uma nova senha.

👉 Link de acesso: http://localhost:8501
"""

            # ✅ Exibir apenas dentro do expander
            with st.expander("📲 Visualizar modelo de mensagem para WhatsApp", expanded=True):
                st.code(texto_whatsapp, language="")


            # ✅ Botão para fechar a mensagem
            if st.button("❌ Fechar esta mensagem", key="fechar_whatsapp"):
                del st.session_state.reenvio_sucesso
                st.rerun()

    # ===== Aplicar Filtros =====
    usuarios_filtrados = []

    for usuario in usuarios:
        # Filtro por busca de texto
        condicao_busca = (
            termo_busca.strip() == "" or
            termo_busca.lower() in usuario.get("nome", "").lower() or
            termo_busca.lower() in usuario.get("cpf", "").lower() or
            termo_busca.lower() in usuario.get("email", "").lower()
        )

        # Filtro por perfil
        condicao_perfil = (filtro_perfil == "Todos" or usuario.get("perfil") == filtro_perfil)

        # Filtro por status
        condicao_status = (
            filtro_status == "Todos" or
            (filtro_status == "Ativos" and usuario.get("ativo")) or
            (filtro_status == "Inativos" and not usuario.get("ativo"))
        )

        if condicao_busca and condicao_perfil and condicao_status:
            usuarios_filtrados.append(usuario)

    # ✅ Mensagem se nenhum resultado após os filtros
    if not usuarios_filtrados:
        st.info("⚠️ Nenhum usuário encontrado com os filtros selecionados.")


    # ===== Paginação =====
    usuarios_por_pagina = 10
    total_paginas = max(1, (len(usuarios_filtrados) - 1) // usuarios_por_pagina + 1)
    pagina_atual = st.session_state.get("pagina_usuarios", 1)

    inicio = (pagina_atual - 1) * usuarios_por_pagina
    fim = inicio + usuarios_por_pagina
    usuarios_paginados = usuarios_filtrados[inicio:fim]

    st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)

    # ===== Cabeçalhos =====
    header_c1, header_c2, header_c3, header_c4, header_c5, header_c6, header_c7, header_c8 = st.columns([3, 2, 3, 2, 1, 1, 1, 1])

    with header_c1: st.markdown("**Nome**")
    with header_c2: st.markdown("**CPF**")
    with header_c3: st.markdown("**Email**")
    with header_c4: st.markdown("**Perfil**")
    with header_c5: st.markdown("**Status**")
    with header_c6: st.markdown("**Senha**")
    with header_c7: st.markdown("**Editar**")
    with header_c8: st.markdown("**Excluir**")

    # ===== Lista de usuários =====
    for usuario in usuarios_paginados:
        col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([3, 2, 3, 2, 1, 1, 1, 1])

        with col1:
            st.write(usuario["nome"])
        with col2:
            st.write(usuario.get("cpf", "—"))
        with col3:
            st.write(usuario.get("email", "—"))
        with col4:
            st.write(usuario.get("perfil") or "Sem Perfil")
        
        with col5:
            status_icon = "✅" if usuario.get("ativo") else "❌"

            if st.button(status_icon, key=f"status_{usuario['id']}", help="Ativar/Desativar", use_container_width=True):
                # ✅ Primeiro: bloquear autoalteração de status, independente de perfil
                if usuario["id"] == st.session_state.usuario_id:
                    st.session_state.show_dialog_auto_status = True
                    st.rerun()

                # ✅ Depois: só Admin pode alterar status de outros usuários
                elif st.session_state.perfil.lower() == "admin":
                    try:
                        resposta_status = requests.patch(
                            f"{API_BASE}/usuarios/{usuario['id']}/status",
                            headers={"Authorization": f"Bearer {st.session_state.token}"}
                        )
                        if resposta_status.status_code == 200:
                            st.success("✅ Status alterado com sucesso.")
                            st.rerun()
                        else:
                            st.error(f"❌ Erro ao alterar status: {resposta_status.text}")
                    except Exception as e:
                        st.error(f"❌ Erro ao conectar com a API: {e}")

                else:
                    # ✅ Agente ou qualquer outro perfil sem permissão
                    st.session_state.show_dialog_sem_permissao_status = True
                    st.rerun()


        with col6:
            redefinir = st.button("🔁", key=f"reenviar_{usuario['id']}", help="Reenviar senha", use_container_width=True)

            if redefinir:
                try:
                    resposta_senha = requests.post(f"{API_BASE}/usuarios/{usuario['id']}/redefinir-senha")
                    if resposta_senha.status_code == 200:
                        # ✅ Seta a flag antes do rerun
                        st.session_state.reenvio_sucesso = usuario["id"]
                        st.rerun()
                    else:
                        st.error("Erro ao redefinir senha.")
                except Exception as e:
                    st.error(f"Erro: {e}")

        with col7:
            if st.button("✏️", key=f"editar_{usuario['id']}", help="Editar usuário", use_container_width=True):
                st.session_state.usuario_id_edicao = usuario["id"]
                st.session_state.pagina = "editar_usuario"
                st.rerun()

        with col8:
            if st.button("🗑", key=f"excluir_{usuario['id']}", help="Excluir usuário", use_container_width=True):
                if usuario["id"] == st.session_state.usuario_id:
                    st.session_state.show_autoexcluir_warning = True
                else:
                    st.session_state.usuario_id_exclusao = usuario["id"]
                    st.session_state.nome_usuario_exclusao = usuario["nome"]
                    st.rerun()



    if "usuario_id_exclusao" in st.session_state:

        @st.dialog(f"⚠️ Confirmar exclusão de {st.session_state.nome_usuario_exclusao}")
        def confirmar_exclusao():
            st.warning(f"Tem certeza que deseja excluir o usuário **{st.session_state.nome_usuario_exclusao}**? Esta ação não poderá ser desfeita.")

            col1, col2 = st.columns(2)

            with col1:
                if st.button("✅ Confirmar Exclusão"):
                    try:
                        delete = requests.delete(
                            f"{API_BASE}/usuarios/{st.session_state.usuario_id_exclusao}",
                            headers={"Authorization": f"Bearer {st.session_state.token}"}
                        )
                        if delete.status_code == 200:
                            st.success("✅ Usuário excluído com sucesso!")
                            del st.session_state.usuario_id_exclusao
                            del st.session_state.nome_usuario_exclusao
                            st.rerun()
                        elif delete.status_code == 403:
                            st.error("❌ Você não tem permissão para excluir usuários.")
                        elif delete.status_code == 401:
                            st.error("❌ Sessão expirada. Faça login novamente.")
                        else:
                            st.error(f"❌ Erro ao excluir usuário: {delete.text}")
                    except Exception as e:
                        st.error(f"❌ Erro: {e}")

            with col2:
                if st.button("❌ Cancelar"):
                    del st.session_state.usuario_id_exclusao
                    del st.session_state.nome_usuario_exclusao
                    st.rerun()

        confirmar_exclusao()

    # ✅ Alerta de autoexclusão
    if st.session_state.get("show_autoexcluir_warning"):
        st.warning("⚠️ Você não pode se autoexcluir enquanto estiver logado no sistema.")
        if st.button("OK", key="fechar_autoexcluir_warning"):
            del st.session_state["show_autoexcluir_warning"]
            st.rerun()

    # ✅ Bloqueio de permissão para agentes
    if st.session_state.get("show_dialog_sem_permissao_status"):
        st.warning("⚠️ Seu perfil não tem permissão para alterar o status de usuários.")
        if st.button("OK", key="fechar_dialog_permissao_status"):
            del st.session_state["show_dialog_sem_permissao_status"]
            st.rerun()

    # ✅ Bloqueio de autoalteração de status
    if st.session_state.get("show_dialog_auto_status"):
        st.warning("⚠️ Você não pode alterar o seu próprio status enquanto estiver logado no sistema.")
        if st.button("OK", key="fechar_dialog_auto_status"):
            del st.session_state["show_dialog_auto_status"]
            st.rerun()

    # ===== Paginação =====
    col_p1, col_p2, col_p3 = st.columns([1, 2, 1])

    with col_p1:
        if st.button("⬅️ Anterior") and pagina_atual > 1:
            st.session_state.pagina_usuarios = pagina_atual - 1
            st.rerun()

    with col_p3:
        if st.button("Próxima ➡️") and pagina_atual < total_paginas:
            st.session_state.pagina_usuarios = pagina_atual + 1
            st.rerun()

    st.markdown(f"Página **{pagina_atual}** de **{total_paginas}**")
