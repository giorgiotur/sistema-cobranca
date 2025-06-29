from app.database import SessionLocal
from app import models

# Cria uma sessão com o banco
db = SessionLocal()

# Perfis que queremos garantir que existam
perfis_iniciais = ["Admin", "Agente", "Cliente"]

# Cria apenas se não existir
for nome in perfis_iniciais:
    existe = db.query(models.Role).filter(models.Role.nome == nome).first()
    if not existe:
        novo_perfil = models.Role(nome=nome)
        db.add(novo_perfil)

db.commit()
db.close()

print("✅ Perfis de acesso inseridos com sucesso!")
