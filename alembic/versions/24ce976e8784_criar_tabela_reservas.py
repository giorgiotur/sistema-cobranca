"""criar tabela reservas

Revision ID: 24ce976e8784
Revises: dd0422e3968e
Create Date: 2025-06-23 23:43:31.691247

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '24ce976e8784'
down_revision: Union[str, None] = 'dd0422e3968e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('reservas',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('numero_reserva_operadora', sa.String(), nullable=False),
    sa.Column('observacoes', sa.String(), nullable=True),
    sa.Column('pagante_id', sa.Integer(), nullable=False),
    sa.Column('pagante_id_asaas', sa.String(), nullable=True),
    sa.Column('parcelas_json', sa.JSON(), nullable=True),
    sa.Column('id_cobranca_asaas', sa.String(), nullable=True),
    sa.Column('status', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['pagante_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reservas_id'), 'reservas', ['id'], unique=False)
    op.alter_column('hoteis', 'id',
               existing_type=sa.NUMERIC(),
               type_=sa.UUID(),
               existing_nullable=False)
    op.create_foreign_key(None, 'orcamentos_pre_pago', 'users', ['created_by_user_id'], ['id'])
    op.alter_column('roles', 'nome',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.drop_index(op.f('ix_roles_nome'), table_name='roles')
    op.add_column('users', sa.Column('data_nascimento', sa.Date(), nullable=True))
    op.alter_column('users', 'senha',
               existing_type=sa.VARCHAR(),
               nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('users', 'senha',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.drop_column('users', 'data_nascimento')
    op.create_index(op.f('ix_roles_nome'), 'roles', ['nome'], unique=1)
    op.alter_column('roles', 'nome',
               existing_type=sa.VARCHAR(),
               nullable=True)
    op.drop_constraint(None, 'orcamentos_pre_pago', type_='foreignkey')
    op.alter_column('hoteis', 'id',
               existing_type=sa.UUID(),
               type_=sa.NUMERIC(),
               existing_nullable=False)
    op.drop_index(op.f('ix_reservas_id'), table_name='reservas')
    op.drop_table('reservas')
    # ### end Alembic commands ###
