from alembic import op
import sqlalchemy as sa

# Revisão Alembic
revision = '23c31ad761cb_add_campo_ativo_ao_user'
down_revision = '19e146eeff4a'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # ✅ Adiciona o campo 'ativo' usando SQL direto (compatível com SQLite)
    op.execute("ALTER TABLE users ADD COLUMN ativo BOOLEAN DEFAULT 1")

def downgrade() -> None:
    # ❌ SQLite não suporta remoção de coluna diretamente
    pass
