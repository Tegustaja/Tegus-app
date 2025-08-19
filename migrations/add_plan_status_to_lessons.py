"""
Migration script to add plan_status field to Lessons table
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'add_plan_status_to_lessons'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    """Add plan_status column to Lessons table"""
    op.add_column('Lessons', sa.Column('plan_status', sa.String(), nullable=True, server_default='creating'))
    
    # Update existing records to have a default plan_status
    op.execute("UPDATE \"Lessons\" SET plan_status = 'ready' WHERE plan_status IS NULL")

def downgrade():
    """Remove plan_status column from Lessons table"""
    op.drop_column('Lessons', 'plan_status')
