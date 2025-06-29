import requests
import re

def buscar_cep(cep: str):
    cep_limpo = re.sub(r'\D', '', cep)
    print(f"DEBUG ViaCEP | Iniciando busca para o CEP: {cep_limpo}")

    try:
        resposta = requests.get(f"https://viacep.com.br/ws/{cep_limpo}/json/")
        print(f"DEBUG ViaCEP | Status HTTP: {resposta.status_code}")
        print(f"DEBUG ViaCEP | Resposta JSON: {resposta.text}")

        if resposta.status_code == 200:
            dados = resposta.json()
            if not dados.get("erro"):
                print(f"DEBUG ViaCEP | Dados válidos recebidos: {dados}")
                return dados
            else:
                print(f"DEBUG ViaCEP | CEP não encontrado no ViaCEP (erro:true)")
        else:
            print(f"DEBUG ViaCEP | Erro HTTP na consulta ao ViaCEP")

    except Exception as e:
        print(f"DEBUG ViaCEP | Exceção ao consultar ViaCEP: {e}")

    return None
