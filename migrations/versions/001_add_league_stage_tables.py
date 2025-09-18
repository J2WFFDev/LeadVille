"""Add league and stage configuration tables

Revision ID: 001
Revises: 
Create Date: 2025-09-17 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create leagues table
    op.create_table('leagues',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('abbreviation', sa.String(10), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('abbreviation')
    )
    op.create_index('idx_league_name', 'leagues', ['name'])

    # Create stage_configs table (template stages independent of matches)
    op.create_table('stage_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('league_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['league_id'], ['leagues.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('league_id', 'name', name='uq_stage_config_league_name')
    )
    op.create_index('idx_stage_config_league', 'stage_configs', ['league_id'])

    # Create target_configs table (template targets for stage configs)
    op.create_table('target_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('stage_config_id', sa.Integer(), nullable=False),
        sa.Column('target_number', sa.Integer(), nullable=False),
        sa.Column('shape', sa.String(50), nullable=False),
        sa.Column('type', sa.String(20), nullable=False),  # Plate, Gong
        sa.Column('category', sa.String(20), nullable=False),  # Primary, Stop, Penalty
        sa.Column('distance_feet', sa.Integer(), nullable=False),
        sa.Column('offset_feet', sa.Float(), nullable=False),  # Offset from centerline
        sa.Column('height_feet', sa.Float(), nullable=False),  # Height from ground
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("type IN ('Plate', 'Gong')", name='check_target_config_type'),
        sa.CheckConstraint("category IN ('Primary', 'Stop', 'Penalty')", name='check_target_config_category'),
        sa.CheckConstraint("distance_feet > 0", name='check_target_config_distance'),
        sa.ForeignKeyConstraint(['stage_config_id'], ['stage_configs.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('stage_config_id', 'target_number', name='uq_target_config_stage_number')
    )
    op.create_index('idx_target_config_stage', 'target_configs', ['stage_config_id'])
    op.create_index('idx_target_config_number', 'target_configs', ['target_number'])

    # Add sensor assignment column to existing sensors table
    op.add_column('sensors', sa.Column('target_config_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_sensor_target_config', 'sensors', 'target_configs', ['target_config_id'], ['id'])
    op.create_index('idx_sensor_target_config', 'sensors', ['target_config_id'])

    # Update existing target table to reference stage configs
    op.add_column('targets', sa.Column('target_config_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_target_target_config', 'targets', 'target_configs', ['target_config_id'], ['id'])


def downgrade():
    # Remove foreign keys and columns
    op.drop_constraint('fk_target_target_config', 'targets', type_='foreignkey')
    op.drop_column('targets', 'target_config_id')
    
    op.drop_index('idx_sensor_target_config', 'sensors')
    op.drop_constraint('fk_sensor_target_config', 'sensors', type_='foreignkey')
    op.drop_column('sensors', 'target_config_id')

    # Drop tables in reverse order
    op.drop_index('idx_target_config_number', 'target_configs')
    op.drop_index('idx_target_config_stage', 'target_configs')
    op.drop_table('target_configs')
    
    op.drop_index('idx_stage_config_league', 'stage_configs')
    op.drop_table('stage_configs')
    
    op.drop_index('idx_league_name', 'leagues')
    op.drop_table('leagues')