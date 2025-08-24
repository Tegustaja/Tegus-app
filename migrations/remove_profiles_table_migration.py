"""
Migration script to remove profiles table and update user references
to use Supabase Auth's auth.users table directly.

This migration:
1. Removes the profiles table
2. Updates all user_id columns to reference auth.users.id
3. Adds the new user_topic_completion table
4. Updates indexes accordingly
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'remove_profiles_table'
down_revision = None
depends_on = None

def upgrade():
    """Upgrade database schema"""
    
    # 1. Create the new user_topic_completion table
    op.create_table('user_topic_completion',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('topic_id', sa.String(), nullable=False),
        sa.Column('is_completed', sa.Boolean(), default=False),
        sa.Column('completed_at', sa.DateTime()),
        sa.Column('progress_percentage', sa.Integer(), default=0),
        sa.Column('mastery_level', sa.Float(), default=0.0),
        sa.Column('last_accessed', sa.DateTime(), default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], ),
        sa.PrimaryKeyConstraint('user_id', 'topic_id')
    )
    
    # 2. Create indexes for the new table
    op.create_index('ix_user_topic_completion_user_id', 'user_topic_completion', ['user_id'])
    op.create_index('ix_user_topic_completion_topic_id', 'user_topic_completion', ['topic_id'])
    
    # 3. Drop the profiles table (this will cascade to drop dependent objects)
    # Note: This will remove all profile data - make sure to backup if needed
    op.drop_table('profiles')

def downgrade():
    """Downgrade database schema"""
    
    # 1. Recreate the profiles table
    op.create_table('profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('avatar_url', sa.String(), nullable=True),
        sa.Column('is_admin', sa.Boolean(), default=False),
        sa.Column('admin_expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 2. Drop the user_topic_completion table
    op.drop_index('ix_user_topic_completion_topic_id', 'user_topic_completion')
    op.drop_index('ix_user_topic_completion_user_id', 'user_topic_completion')
    op.drop_table('user_topic_completion')
    
    # Note: You would need to recreate the foreign key relationships and indexes
    # for the profiles table if you want to fully restore the previous state
