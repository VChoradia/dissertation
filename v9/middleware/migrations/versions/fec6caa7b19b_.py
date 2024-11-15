"""empty message

Revision ID: fec6caa7b19b
Revises: 750a0bdf717c
Create Date: 2024-04-07 12:22:45.893993

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'fec6caa7b19b'
down_revision = '750a0bdf717c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('devices', schema=None) as batch_op:
        batch_op.alter_column('organization_id',
               existing_type=mysql.INTEGER(),
               nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('devices', schema=None) as batch_op:
        batch_op.alter_column('organization_id',
               existing_type=mysql.INTEGER(),
               nullable=False)

    # ### end Alembic commands ###
