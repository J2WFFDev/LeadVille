"""Add Bridge table and bridge_id to sensors

Revision ID: 002_add_bridge_support
Revises: 001_add_league_stage_tables
Create Date: 2025-09-18 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func

# revision identifiers
revision = '002_add_bridge_support'
down_revision = '001_add_league_stage_tables'
branch_labels = None
depends_on = None


def upgrade():
    """Add Bridge table and bridge_id to sensors for Bridge-centric ownership"""
    
    # Create bridges table
    op.create_table('bridges',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('bridge_id', sa.String(length=50), nullable=False),
        sa.Column('current_stage_id', sa.Integer(), nullable=True),
        sa.Column('match_id', sa.String(length=100), nullable=True),
        sa.Column('match_name', sa.String(length=200), nullable=True),
        sa.Column('node_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=func.now()),
        sa.ForeignKeyConstraint(['current_stage_id'], ['stage_configs.id'], ),
        sa.ForeignKeyConstraint(['node_id'], ['nodes.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('bridge_id')
    )
    
    # Create indexes for bridges table
    op.create_index('idx_bridge_name', 'bridges', ['name'], unique=False)
    op.create_index('idx_bridge_id', 'bridges', ['bridge_id'], unique=False)
    op.create_index('idx_bridge_stage', 'bridges', ['current_stage_id'], unique=False)
    
    # Add bridge_id column to sensors table
    op.add_column('sensors', sa.Column('bridge_id', sa.Integer(), nullable=True))
    
    # Create foreign key constraint for sensors.bridge_id
    op.create_foreign_key('fk_sensors_bridge_id', 'sensors', 'bridges', ['bridge_id'], ['id'])
    
    # Create index for sensors.bridge_id
    op.create_index('idx_sensor_bridge', 'sensors', ['bridge_id'], unique=False)
    
    # Create a default Bridge for existing data migration
    op.execute("""
        INSERT INTO bridges (name, bridge_id, created_at, updated_at) 
        VALUES ('Default Bridge', 'bridge-001', datetime('now'), datetime('now'))
    """)
    
    # Assign existing sensors to the default Bridge
    op.execute("""
        UPDATE sensors 
        SET bridge_id = (SELECT id FROM bridges WHERE bridge_id = 'bridge-001' LIMIT 1)
        WHERE bridge_id IS NULL
    """)


def downgrade():
    """Remove Bridge support"""
    
    # Remove bridge_id from sensors
    op.drop_constraint('fk_sensors_bridge_id', 'sensors', type_='foreignkey')
    op.drop_index('idx_sensor_bridge', table_name='sensors')
    op.drop_column('sensors', 'bridge_id')
    
    # Drop bridges table indexes
    op.drop_index('idx_bridge_stage', table_name='bridges')
    op.drop_index('idx_bridge_id', table_name='bridges')
    op.drop_index('idx_bridge_name', table_name='bridges')
    
    # Drop bridges table
    op.drop_table('bridges')