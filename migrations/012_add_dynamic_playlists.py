"""
Migration: Add Dynamic Playlists Support
Date: August 23, 2025
Issue: #109 - Dynamic Playlists

This migration adds fields to the playlists table to support dynamic playlists
with filter criteria and automatic updating.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mysql import JSON


def upgrade():
    """Add dynamic playlist fields to playlists table"""
    
    # Add new columns to playlists table
    with op.batch_alter_table('playlists', schema=None) as batch_op:
        # Add playlist type column with default STATIC
        batch_op.add_column(
            sa.Column('playlist_type', 
                     sa.Enum('STATIC', 'DYNAMIC', name='playlisttype'), 
                     server_default='STATIC', 
                     nullable=False)
        )
        
        # Add filter criteria JSON column
        batch_op.add_column(
            sa.Column('filter_criteria', JSON, nullable=True)
        )
        
        # Add auto_update column with default True
        batch_op.add_column(
            sa.Column('auto_update', sa.Boolean, 
                     server_default='1', 
                     nullable=False)
        )
        
        # Add last_updated timestamp column
        batch_op.add_column(
            sa.Column('last_updated', sa.DateTime, nullable=True)
        )

    # Add indexes for dynamic playlist functionality
    op.create_index('idx_playlist_type', 'playlists', ['playlist_type'])
    op.create_index('idx_playlist_auto_update', 'playlists', ['auto_update'])
    op.create_index('idx_playlist_last_updated', 'playlists', ['last_updated'])
    op.create_index('idx_playlist_type_auto', 'playlists', ['playlist_type', 'auto_update'])


def downgrade():
    """Remove dynamic playlist fields from playlists table"""
    
    # Remove indexes
    op.drop_index('idx_playlist_type_auto', 'playlists')
    op.drop_index('idx_playlist_last_updated', 'playlists')
    op.drop_index('idx_playlist_auto_update', 'playlists')
    op.drop_index('idx_playlist_type', 'playlists')
    
    # Remove columns
    with op.batch_alter_table('playlists', schema=None) as batch_op:
        batch_op.drop_column('last_updated')
        batch_op.drop_column('auto_update')
        batch_op.drop_column('filter_criteria')
        batch_op.drop_column('playlist_type')

    # Drop the enum type if needed (MySQL specific)
    op.execute("DROP TYPE IF EXISTS playlisttype")