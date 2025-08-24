# Database Migration: Remove Profiles Table

This migration removes the `profiles` table and updates all user references to use Supabase Auth's `auth.users` table directly.

## What This Migration Does

1. **Removes the `profiles` table** - Since you're using Supabase Auth, you don't need a separate profiles table
2. **Updates all `user_id` columns** - Removes foreign key constraints to `profiles.id` and references `auth.users.id` directly
3. **Adds `user_topic_completion` table** - New table to track which topics each user has completed
4. **Enables Row Level Security (RLS)** - Ensures users can only access their own data
5. **Creates automatic triggers** - Automatically creates completion records when lessons start and updates them when completed

## Files Created

- `remove_profiles_table_migration.py` - Alembic migration script
- `remove_profiles_table.sql` - Direct SQL script for Supabase
- `test_database_structure.py` - Test script to verify the changes

## How to Apply the Migration

### Option 1: Using Supabase SQL Editor (Recommended)

1. Go to your Supabase dashboard
2. Navigate to the SQL Editor
3. Copy and paste the contents of `remove_profiles_table.sql`
4. Run the script

### Option 2: Using Alembic

1. Make sure you have Alembic installed: `pip install alembic`
2. Run: `alembic upgrade head`

## What Happens After Migration

### Before Migration
```
profiles table exists with user data
All tables reference profiles.id via foreign keys
No topic completion tracking
```

### After Migration
```
profiles table is removed
All tables reference auth.users.id directly (no foreign keys)
user_topic_completion table tracks topic completion
RLS policies ensure data security
Automatic triggers maintain completion data
```

## New Table Structure

### `user_topic_completion`
```sql
CREATE TABLE user_topic_completion (
    user_id UUID NOT NULL,           -- References auth.users.id
    topic_id TEXT NOT NULL,          -- References topics.id
    is_completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP WITH TIME ZONE,
    progress_percentage INTEGER DEFAULT 0,  -- 0-100
    mastery_level DOUBLE PRECISION DEFAULT 0.0,  -- 0.0-1.0
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    PRIMARY KEY (user_id, topic_id)
);
```

## Automatic Features

### 1. Completion Record Creation
When a user starts a lesson, a completion record is automatically created in `user_topic_completion`.

### 2. Completion Status Updates
When a lesson is marked as completed, the completion record is automatically updated with:
- `is_completed = TRUE`
- `completed_at = current timestamp`
- `progress_percentage = 100`
- `mastery_level = 1.0`

### 3. Row Level Security
Users can only access their own completion data through the RLS policy:
```sql
CREATE POLICY "Users can only access their own topic completion data" 
ON user_topic_completion 
FOR ALL 
USING (auth.uid() = user_id);
```

## Testing the Migration

Run the test script to verify everything works:
```bash
python3 test_database_structure.py
```

## Rollback (If Needed)

If you need to rollback, you can:
1. Restore from a database backup
2. Or manually recreate the profiles table and restore the old structure

## Benefits

1. **Cleaner Schema** - No duplicate user data
2. **Better Security** - RLS policies ensure data isolation
3. **Automatic Tracking** - Topic completion is tracked automatically
4. **Supabase Integration** - Leverages built-in auth system
5. **Performance** - Direct references to auth.users table

## Next Steps

After running the migration:

1. **Update your application code** to use the new models
2. **Test the new functionality** - topic completion tracking
3. **Update any queries** that previously joined with the profiles table
4. **Verify RLS policies** are working correctly

## Important Notes

- **Backup your database** before running this migration
- **Test in development** first
- **Update your application code** to handle the new structure
- **Verify all functionality** works as expected after migration
