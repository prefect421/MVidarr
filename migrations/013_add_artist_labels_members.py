"""
Migration: Add Artist Labels and Members Fields
Date: August 28, 2025
Issue: Fix missing keywords, genres, record labels, and band members display issue

This migration adds labels and members fields to the artists table.
The labels field stores record labels as JSON, and members field stores band members as text.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mysql import JSON


def upgrade():
    """Add labels and members fields to artists table"""
    
    # Add new columns to artists table
    with op.batch_alter_table('artists', schema=None) as batch_op:
        # Add labels column for record labels (JSON)
        batch_op.add_column(
            sa.Column('labels', JSON, nullable=True, comment='Record labels associated with the artist')
        )
        
        # Add members column for band members (Text)
        batch_op.add_column(
            sa.Column('members', sa.Text, nullable=True, comment='Band members (stored as text)')
        )


def downgrade():
    """Remove labels and members fields from artists table"""
    
    # Remove columns
    with op.batch_alter_table('artists', schema=None) as batch_op:
        batch_op.drop_column('members')
        batch_op.drop_column('labels')