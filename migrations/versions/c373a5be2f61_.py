"""empty message

Revision ID: c373a5be2f61
Revises: 538cade41d3b
Create Date: 2020-06-12 16:55:21.256057

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c373a5be2f61'
down_revision = '538cade41d3b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('shows')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('shows',
    sa.Column('artists_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('venue_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('show_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['artists_id'], ['Artist.id'], name='shows_artists_id_fkey'),
    sa.ForeignKeyConstraint(['venue_id'], ['Venue.id'], name='shows_venue_id_fkey')
    )
    # ### end Alembic commands ###
