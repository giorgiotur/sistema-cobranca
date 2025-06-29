import streamlit as st
import base64
from pathlib import Path
from components.botao_menu import botao_menu  # <- agora sim corretamente!
from utils.navigation import ir_para

# ===== MENU LATERAL =====
def menu_lateral():
    with st.sidebar:
        st.markdown("""
        <style>
        /* 📂 Sidebar - expanders */
        section[data-testid="stSidebar"] {
            background-color: #f5f8fa;
            border-right: 0px solid #dee2e6;
            padding-top: 10px;
        }

        section[data-testid="stSidebar"] details summary {
            background-color: #e6f0ff;
            color: #0033cc;
            padding: 10px;
            margin-top: 6px;
            margin-bottom: 4px;
            border-radius: 6px;
            font-weight: bold;
            text-transform: uppercase;
            font-size: 12px;
            letter-spacing: 0.5px;
        }

        section[data-testid="stSidebar"] details[open] summary {
            background-color: #;
        }

        section[data-testid="stSidebar"] details summary span {
            font-size: 0px;
        }

        /* 🟦 Botões do menu lateral */
        section[data-testid="stSidebar"] button[kind="secondary"] {
            box-sizing: border-box;
            display: block;
            width: 100%;
            padding: 10px 14px;
            margin: 4px 0;
            font-size: 12px;
            font-weight: 800;
            color: #212529;
            background-color: white;
            border: 1px solid #cfdfff;
            border-radius: 6px;
            text-align: justify;
            text-transform: uppercase;
            cursor: pointer;
            transition: background-color 0.2s ease;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }

        section[data-testid="stSidebar"] button[kind="secondary"]:hover {
            background-color: #dceaff;
            color: #1a54ba;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }

        section[data-testid="stSidebar"] button[kind="secondary"] > div {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 12px;
        }

        /* 🔧 Botões pequenos (Meu Cadastro, Alterar Senha) */
        .perfil-btns .stButton > button {
            font-size: 10px;
            white-space: nowrap;
            padding: 6px 10px;
        }
        </style>
    """, unsafe_allow_html=True)

        nome_usuario = st.session_state.get("nome", "Usuário")
        perfil_usuario = st.session_state.get("perfil", "admin").capitalize()
        usuario_id = st.session_state.get("usuario_id", "default")

        caminho_foto = Path(f"imagens/{usuario_id}.png")
        if not caminho_foto.exists():
            caminho_foto = Path("imagens/padrao.png")

        # 📷 Foto com classe CSS aplicada e sem quebra
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with open(caminho_foto, "rb") as f:
                image_base64 = base64.b64encode(f.read()).decode()

            st.markdown(f"""
                <style>
                    .foto-perfil {{
                        border: 3px solid #1f77b4;
                        border-radius: 50%;
                        width: 104px;
                        height: 104px;
                        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
                        object-fit: cover;
                        display: block;
                        margin-left: auto;
                        margin-right: auto;
                    }}
                </style>
                <img src="data:image/png;base64,{image_base64}" class="foto-perfil"/>
            """, unsafe_allow_html=True)

        # 👋 Saudação
        st.markdown(f"""
            <div style='text-align:center; margin-top: 10px; font-size: 15px;'>
                👋 Seja bem-vindo, <strong>{nome_usuario}</strong>
            </div>
        """, unsafe_allow_html=True)

        # 🔘 Botões com estilo específico, texto pequeno e inline
        st.markdown('<div class="perfil-btns">', unsafe_allow_html=True)

        col_btn1, col_btn2 = st.columns([1, 1])
        with col_btn1:
            if st.button("🧍 MEU CADASTRO", key="btn_meu_cadastro", use_container_width=True):
                ir_para("meus_dados")

        with col_btn2:
            if st.button("🔐 ALTERAR SENHA", key="btn_alterar_senha", use_container_width=True):
                ir_para("alterar_senha")

        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown(f"""
            <div class='perfil-status'>
                🟢 <strong>Status:</strong> Logado<br>
                🔑 <strong>Acesso:</strong> {perfil_usuario}
            </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        with st.expander("⚙️ configuração", expanded=True):
            botao_menu("Cadastro Empresa", "🏢", "empresa")

        with st.expander("📦 Pacotes Pré Pago", expanded=True):
            botao_menu("Pacote Pré Pago", "📁", "Pacote Pre_Pago")
            botao_menu("Criação Novo Pacote", "🆕", "Novo_Pacote")
            botao_menu("Pacote Contratado", "✅", "Pacote_Contratado")

        with st.expander("📦 Hospedagem Pré Paga", expanded=True):
            botao_menu("Orçamento - Pré-pago", "🧾", "orcamento_pre_pago")
            botao_menu("Consulta de Orçamento", "🔎", "consultar_orcamento")
            botao_menu("Consultar Vendas", "💳", "consultar_pacotes")

        with st.expander("📝 Cadastro de cliente", expanded=True):
            botao_menu("Novo Cliente", "🧾", "novo_cliente")
            botao_menu("Consultar Cliente", "🔎", "consultar_cliente")

        with st.expander("👤 Usuário do sistema", expanded=True):
            #botao_menu("Criar Usuário", "👤", "novo_usuario")
            botao_menu("Usuário do Sistema", "📋", "lista_usuarios")

        with st.expander("💳 Cobrança e pagamento", expanded=True):
            botao_menu("Criar Cobrança", "➕", "Criar Cobrança")
            botao_menu("Cobrança Avulsa", "💵", "Cobrança Avulsa")

        with st.expander("📄 Extrato de pagamento", expanded=True):
            botao_menu("Extrato Total", "📑", "Extrato Total")
            botao_menu("Parcelas Pagas", "✅", "Parcelas Pagas")
            botao_menu("Parcelas em Aberto", "⏳", "Parcelas em Aberto")

        with st.expander("📊 Relatórios", expanded=True):
            botao_menu("Relatório Geral", "📊", "Relatorio Geral")
            botao_menu("Relatório Mensal", "📈", "Relatorio Mensal")

            st.markdown("---")
            if st.button("🚪 Sair do Sistema"):
                 ir_para("logout", logout=True)