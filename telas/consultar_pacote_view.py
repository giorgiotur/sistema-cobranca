import streamlit as st
import requests
import os
import re
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
API_BASE = os.getenv("API_BASE", "http://localhost:8000")
ASAAS_API_BASE = os.getenv("ASAAS_API_BASE", "https://sandbox.asaas.com")


def tela_consultar_pacotes():
    st.title("📦 Consulta de Pacote Contratado")

    token = st.session_state.get("token")
    if not token:
        st.warning("⚠️ Usuário não autenticado.")
        return
    headers = {"Authorization": f"Bearer {token}"}

    # 🔁 Se o CPF veio da tela de orçamentos (botão "Vendido")
    if "cpf_orcamento" in st.session_state:
        st.session_state["cpf_pacote"] = st.session_state.pop("cpf_orcamento")

    # 🔹 Layout do input de CPF centralizado
    col_esq, col_input, col_dir = st.columns([3, 4, 3])
    with col_input:
        cpf = st.text_input(
            "Informe o CPF do cliente:",
            value=st.session_state.get("cpf_pacote", ""),
            key="cpf_pacote"
        )

    # 🔘 Botão buscar centralizado
    _, col_btn, _ = st.columns([4.5, 3, 4.5])
    with col_btn:
        buscar = st.button("🔎 Buscar Reserva")

    # 🚀 Executa busca se clicar no botão ou se CPF veio de outra tela
    if buscar or (st.session_state.get("cpf_pacote") and not st.session_state.get("buscou_pacote")):
        st.session_state["buscou_pacote"] = True
        st.rerun()

    # ⛔ Caso não haja CPF, não prossegue
    if "cpf_pacote" not in st.session_state or not st.session_state["cpf_pacote"]:
        return

    cpf_limpo = re.sub(r'\D', '', st.session_state["cpf_pacote"])

    try:
        url_cliente = f"{API_BASE}/clientes/por-cpf/{cpf_limpo}"
        response_cliente = requests.get(url_cliente, headers=headers)
    except Exception as e:
        st.error(f"Erro ao buscar cliente: {e}")
        return

    if response_cliente.status_code != 200:
        st.warning("❌ Cliente não encontrado.")
        return

    cliente = response_cliente.json()

    url_reserva = f"{API_BASE}/reservas/por-cliente/{cliente['id']}"
    response_reserva = requests.get(url_reserva, headers=headers)
    if response_reserva.status_code != 200:
        st.warning("❌ Nenhuma reserva encontrada.")
        return

    reservas = response_reserva.json()
    if not reservas:
        st.warning("⚠️ Cliente não possui reservas.")
        return

    reserva = reservas[0]
    orcamento = reserva.get("orcamento", {})

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 👤 Dados do Cliente")
        st.markdown(f"**Nome:** {cliente.get('nome', '—')}")
        st.markdown(f"**CPF:** {cliente.get('cpf', '—')}")
        st.markdown(f"**Data de Nascimento:** {cliente.get('data_nascimento', '—')}")
        st.markdown(f"**Email:** {cliente.get('email', '—')}")
        st.markdown(f"**Telefone:** {cliente.get('telefone', '—')}")
        st.markdown(f"**CEP:** {cliente.get('cep', '—')}")
        st.markdown(f"**Endereço:** {cliente.get('rua', '')}, {cliente.get('numero', '')}, {cliente.get('bairro', '')}")
        st.markdown(f"**Cidade/Estado:** {cliente.get('cidade', '')} - {cliente.get('estado', '')}")

    with col2:
        st.markdown("### 🏨 Dados da Reserva")
        st.markdown(f"**Número do Orçamento:** {orcamento.get('numero_orcamento', '—')}")
        st.markdown(f"**Destino:** {orcamento.get('destino', '—')}")
        st.markdown(f"**Hotel:** {orcamento.get('nome_hotel', '—')}")

        checkin = orcamento.get("data_ida")
        checkout = orcamento.get("data_volta")

        def formatar_data(data_str):
            try:
                return datetime.strptime(data_str, "%Y-%m-%d").strftime("%d/%m/%Y")
            except:
                return data_str or "—"

        st.markdown(f"**Check-in:** {formatar_data(checkin)}")
        st.markdown(f"**Check-out:** {formatar_data(checkout)}")
        st.markdown(f"**Valor Total:** R$ {orcamento.get('valor_total', 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        st.markdown(f"**Operadora:** {reserva.get('operadora', '—')}")
        st.markdown(f"**Número Reserva Operadora:** {reserva.get('numero_reserva_operadora', '—')}")
        st.markdown(f"**Observações:** {reserva.get('observacoes', '—')}")

    st.markdown("---")
    st.markdown("### 📑 Boletos Gerados")

    url_boletos = f"{ASAAS_API_BASE}/api/v3/payments?externalReference={reserva.get('id')}"
    headers_boletos = {
        "Content-Type": "application/json",
        "access_token": os.getenv("ASAAS_API_KEY")
    }

    try:
        resp_boletos = requests.get(url_boletos, headers=headers_boletos)
        if resp_boletos.status_code == 200:
            boletos = resp_boletos.json().get("data", [])
            if boletos:
                boletos.sort(key=lambda b: datetime.strptime(b.get("dueDate", "2100-12-31"), "%Y-%m-%d"))
                st.markdown("""
                    <style>
                        table { width: 100%; border-collapse: collapse; font-family: sans-serif; margin-top: 1em; }
                        th, td { padding: 10px; border: 1px solid #ddd; text-align: left; }
                        th { background-color: #f5f5f5; }
                        td.acao a { margin-right: 8px; text-decoration: none; font-size: 14px; }
                    </style>
                """, unsafe_allow_html=True)

                tabela = "<table><thead><tr><th>Nome</th><th>Valor</th><th>Descrição</th><th>Forma de pagamento</th><th>Vencimento</th><th>Ações</th></tr></thead><tbody>"
                for b in boletos:
                    nome = cliente.get("nome", "—")
                    valor = f"R$ {float(b['value']):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    desc = b.get("description", "—")
                    tipo = b.get("billingType", "—")
                    venc = b.get("dueDate", "—")
                    url = b.get("invoiceUrl", "#")
                    acoes = f"""
                        <td class='acao'>
                            <a href="{url}" target="_blank" title="Imprimir">🖨️</a>
                            <a href="{url}" target="_blank" title="Download">⬇️</a>
                        </td>
                    """
                    tabela += f"<tr><td>{nome}</td><td>{valor}</td><td>{desc}</td><td>{tipo}</td><td>{venc}</td>{acoes}</tr>"
                tabela += "</tbody></table>"
                st.markdown(tabela, unsafe_allow_html=True)
            else:
                st.info("Nenhum boleto encontrado.")
        else:
            st.warning("Erro ao buscar boletos.")
    except Exception as e:
        st.error(f"Erro inesperado ao buscar boletos: {e}")

        st.markdown("---")

    st.markdown("### 📄 Contrato")

    col_a, col_b, col_c, col_d, col_e = st.columns([1, 2, 2, 2, 1])
    with col_b:
        st.markdown(f"""
            <a href="{API_BASE}/reservas/{reserva['id']}/contrato?formato=html&modo=visualizar">
                <button style='width:100%; padding:10px; background-color:white; border-radius:8px; border:1px solid #ccc;'>📝 Visualizar</button>
            </a>
        """, unsafe_allow_html=True)

    with col_c:
        st.markdown(f"""
            <a href="{API_BASE}/reservas/{reserva['id']}/contrato?formato=pdf" target="_blank">
                <button style='width:100%; padding:10px; background-color:white; border-radius:8px; border:1px solid #ccc;'>🖨️ Imprimir</button>
            </a>
        """, unsafe_allow_html=True)

    with col_d:
        st.markdown(f"""
            <a href="{API_BASE}/reservas/{reserva['id']}/contrato?formato=pdf" target="_blank">
                <button style='width:100%; padding:10px; background-color:white; border-radius:8px; border:1px solid #ccc;'>⬇️ Download</button>
            </a>
        """, unsafe_allow_html=True)

    st.markdown("---")
    _, col_voltar, _ = st.columns([4, 2, 4])
    with col_voltar:
        if st.button("🔙 Voltar"):
            st.session_state.pagina = "consultar_orcamento"
            st.session_state.pop("cpf_pacote", None)
            st.session_state.pop("buscou_pacote", None)
            st.rerun()
