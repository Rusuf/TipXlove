"""Add mpesa_request_id to Withdrawal model

Revision ID: c1175b755420
Revises: 
Create Date: 2025-04-03 16:20:01.849266

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c1175b755420'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('withdrawal', schema=None) as batch_op:
        batch_op.add_column(sa.Column('mpesa_request_id', sa.String(length=50), nullable=True))
        batch_op.create_index('idx_withdrawal_mpesa_request', ['mpesa_request_id'], unique=False)
        batch_op.create_unique_constraint('uq_withdrawal_mpesa_request_id', ['mpesa_request_id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('withdrawal', schema=None) as batch_op:
        batch_op.drop_constraint('uq_withdrawal_mpesa_request_id', type_='unique')
        batch_op.drop_index('idx_withdrawal_mpesa_request')
        batch_op.drop_column('mpesa_request_id')

    # ### end Alembic commands ###
