"""empty message

Revision ID: 412f5bd2d795
Revises: 41341cc8c5b5
Create Date: 2020-06-15 11:23:45.219772

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '412f5bd2d795'
down_revision = '41341cc8c5b5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Artist', sa.Column('seeking_venue', sa.Boolean(), nullable=True))
    op.drop_column('Artist', 'seeking_talent')
    op.add_column('Venue', sa.Column('seeking_talent', sa.Boolean(), nullable=True))
    op.drop_column('Venue', 'seeking_venue')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Venue', sa.Column('seeking_venue', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.drop_column('Venue', 'seeking_talent')
    op.add_column('Artist', sa.Column('seeking_talent', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.drop_column('Artist', 'seeking_venue')
    # ### end Alembic commands ###
