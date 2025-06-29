import streamlit as st

st.title("Teste de Modal de Exclusão")

# Verificar se o botão foi clicado
if st.button("🗑 Excluir usuário de exemplo"):
    st.session_state.nome_usuario_exclusao = "Usuário Exemplo"
    st.session_state.abrir_modal = True

# Só abre o modal se a flag estiver setada
if st.session_state.get("abrir_modal"):
    with st.modal(f"⚠️ Confirmar exclusão de {st.session_state.nome_usuario_exclusao}"):
        st.warning(f"Tem certeza que deseja excluir o usuário **{st.session_state.nome_usuario_exclusao}**? Esta ação não poderá ser desfeita.")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("✅ Confirmar Exclusão"):
                st.success(f"✅ Usuário {st.session_state.nome_usuario_exclusao} excluído com sucesso!")
                del st.session_state.abrir_modal
                st.rerun()

        with col2:
            if st.button("❌ Cancelar"):
                del st.session_state.abrir_modal
                st.rerun()
