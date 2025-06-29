import re
import secrets

def validar_cpf(cpf: str) -> bool:
    return len(re.sub(r'\D', '', cpf)) == 11

def validar_telefone(telefone: str) -> bool:
    return len(re.sub(r'\D', '', telefone)) in [10, 11]

def validar_cep(cep: str) -> bool:
    return len(re.sub(r'\D', '', cep)) == 8

def validar_email(email: str) -> bool:
    return "@" in email and "." in email and not email.isspace()

def gerar_token_unico():
    return secrets.token_urlsafe(48)

def validar_forca_senha(senha: str):
    erros = []
    if len(senha) < 8:
        erros.append("A senha deve ter pelo menos 8 caracteres.")
    if not any(c.isupper() for c in senha):
        erros.append("A senha deve ter pelo menos uma letra maiúscula.")
    if not any(c.isdigit() for c in senha):
        erros.append("A senha deve ter pelo menos um número.")
    if not any(c in "!@#$%^&*()-_=+[]{}|;:'\",.<>?/" for c in senha):
        erros.append("A senha deve ter pelo menos um caractere especial.")
    return erros
