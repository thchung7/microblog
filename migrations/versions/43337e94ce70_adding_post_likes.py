"""adding post likes

Revision ID: 43337e94ce70
Revises: ddb5ba6d4feb
Create Date: 2023-07-17 15:39:15.489227

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '43337e94ce70'
down_revision = 'ddb5ba6d4feb'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('post_like',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('post_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['post_id'], ['post.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('post_like')
    # ### end Alembic commands ###
