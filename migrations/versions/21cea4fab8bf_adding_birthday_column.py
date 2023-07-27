"""adding birthday column

Revision ID: 21cea4fab8bf
Revises: 7a2bc20aa6b2
Create Date: 2023-07-13 08:58:19.240356

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '21cea4fab8bf'
down_revision = '7a2bc20aa6b2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('birthday', sa.Date(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('birthday')

    # ### end Alembic commands ###