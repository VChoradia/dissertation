"""Added threshold columns to UserDetail

Revision ID: 5ae418004aa6
Revises: 
Create Date: 2024-04-01 13:06:56.803147

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5ae418004aa6'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user_detail', schema=None) as batch_op:
        batch_op.add_column(sa.Column('bpm_upper_threshold', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('bpm_lower_threshold', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('temperature_upper_threshold', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('temperature_lower_threshold', sa.Integer(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user_detail', schema=None) as batch_op:
        batch_op.drop_column('temperature_lower_threshold')
        batch_op.drop_column('temperature_upper_threshold')
        batch_op.drop_column('bpm_lower_threshold')
        batch_op.drop_column('bpm_upper_threshold')

    # ### end Alembic commands ###
