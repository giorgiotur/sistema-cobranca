import re

def formatar_cpf(cpf: str) -> str:
    cpf = re.sub(r'\D', '', cpf)
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}" if len(cpf) == 11 else cpf

def formatar_telefone(telefone: str) -> str:
    telefone = re.sub(r'\D', '', telefone)
    if len(telefone) == 11:
        return f"({telefone[:2]}) {telefone[2:7]}-{telefone[7:]}"
    elif len(telefone) == 10:
        return f"({telefone[:2]}) {telefone[2:6]}-{telefone[6:]}"
    return telefone

def formatar_cep(cep: str) -> str:
    cep = re.sub(r'\D', '', cep)
    return f"{cep[:5]}-{cep[5:]}" if len(cep) == 8 else cep
