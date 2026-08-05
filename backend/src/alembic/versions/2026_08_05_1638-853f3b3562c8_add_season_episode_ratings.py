"""add_season_episode_ratings

Revision ID: 853f3b3562c8
Revises: f3b6c0e4a123
Create Date: 2026-08-05 16:38:30.802216

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '853f3b3562c8'
down_revision: Union[str, Sequence[str], None] = 'f3b6c0e4a123'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


user_title_status_enum = postgresql.ENUM(
    'COMPLETED',
    'PLAYING',
    'WATCHING',
    'DROPPED',
    'PLANNED',
    'ON_HOLD',
    name='usertitlestatus',
    create_type=False,
)


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'title_seasons',
        sa.Column('title_id', sa.Integer(), nullable=False),
        sa.Column('season_number', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('episode_count', sa.Integer(), nullable=True),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ['title_id'],
            ['titles.id'],
            name=op.f('fk_title_seasons_title_id_titles'),
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_title_seasons')),
        sa.UniqueConstraint('title_id', 'season_number', name='uq_title_season'),
    )
    op.create_index(
        op.f('ix_title_seasons_title_id'),
        'title_seasons',
        ['title_id'],
        unique=False,
    )
    op.create_table(
        'title_episodes',
        sa.Column('title_season_id', sa.Integer(), nullable=False),
        sa.Column('episode_number', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=512), nullable=True),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ['title_season_id'],
            ['title_seasons.id'],
            name=op.f('fk_title_episodes_title_season_id_title_seasons'),
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_title_episodes')),
        sa.UniqueConstraint(
            'title_season_id', 'episode_number', name='uq_title_episode'
        ),
    )
    op.create_index(
        op.f('ix_title_episodes_title_season_id'),
        'title_episodes',
        ['title_season_id'],
        unique=False,
    )
    op.create_table(
        'user_title_seasons',
        sa.Column('user_title_id', sa.Integer(), nullable=False),
        sa.Column('title_season_id', sa.Integer(), nullable=False),
        sa.Column('status', user_title_status_enum, nullable=False),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('avg_score', sa.Float(), nullable=True),
        sa.Column(
            'score_is_manual',
            sa.Boolean(),
            server_default='false',
            nullable=False,
        ),
        sa.Column('review_text', sa.Text(), nullable=True),
        sa.Column(
            'is_spoiler', sa.Boolean(), server_default='false', nullable=False
        ),
        sa.Column(
            'created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False
        ),
        sa.Column(
            'updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False
        ),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ['title_season_id'],
            ['title_seasons.id'],
            name=op.f('fk_user_title_seasons_title_season_id_title_seasons'),
            ondelete='CASCADE',
        ),
        sa.ForeignKeyConstraint(
            ['user_title_id'],
            ['user_titles.id'],
            name=op.f('fk_user_title_seasons_user_title_id_user_titles'),
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_user_title_seasons')),
        sa.UniqueConstraint(
            'user_title_id', 'title_season_id', name='uq_user_title_season'
        ),
    )
    op.create_index(
        op.f('ix_user_title_seasons_title_season_id'),
        'user_title_seasons',
        ['title_season_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_user_title_seasons_user_title_id'),
        'user_title_seasons',
        ['user_title_id'],
        unique=False,
    )
    op.create_table(
        'user_title_episodes',
        sa.Column('user_title_season_id', sa.Integer(), nullable=False),
        sa.Column('title_episode_id', sa.Integer(), nullable=False),
        sa.Column('status', user_title_status_enum, nullable=False),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column(
            'created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False
        ),
        sa.Column(
            'updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False
        ),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ['title_episode_id'],
            ['title_episodes.id'],
            name=op.f('fk_user_title_episodes_title_episode_id_title_episodes'),
            ondelete='CASCADE',
        ),
        sa.ForeignKeyConstraint(
            ['user_title_season_id'],
            ['user_title_seasons.id'],
            name=op.f(
                'fk_user_title_episodes_user_title_season_id_user_title_seasons'
            ),
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_user_title_episodes')),
        sa.UniqueConstraint(
            'user_title_season_id',
            'title_episode_id',
            name='uq_user_title_episode',
        ),
    )
    op.create_index(
        op.f('ix_user_title_episodes_title_episode_id'),
        'user_title_episodes',
        ['title_episode_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_user_title_episodes_user_title_season_id'),
        'user_title_episodes',
        ['user_title_season_id'],
        unique=False,
    )
    op.add_column('user_titles', sa.Column('avg_score', sa.Float(), nullable=True))
    op.add_column(
        'user_titles',
        sa.Column(
            'score_is_manual',
            sa.Boolean(),
            server_default='false',
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('user_titles', 'score_is_manual')
    op.drop_column('user_titles', 'avg_score')
    op.drop_index(
        op.f('ix_user_title_episodes_user_title_season_id'),
        table_name='user_title_episodes',
    )
    op.drop_index(
        op.f('ix_user_title_episodes_title_episode_id'),
        table_name='user_title_episodes',
    )
    op.drop_table('user_title_episodes')
    op.drop_index(
        op.f('ix_user_title_seasons_user_title_id'),
        table_name='user_title_seasons',
    )
    op.drop_index(
        op.f('ix_user_title_seasons_title_season_id'),
        table_name='user_title_seasons',
    )
    op.drop_table('user_title_seasons')
    op.drop_index(
        op.f('ix_title_episodes_title_season_id'), table_name='title_episodes'
    )
    op.drop_table('title_episodes')
    op.drop_index(op.f('ix_title_seasons_title_id'), table_name='title_seasons')
    op.drop_table('title_seasons')
