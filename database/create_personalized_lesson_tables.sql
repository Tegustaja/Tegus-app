-- SQL script to create the personalized lesson structure tables
-- This script creates all the new tables needed for the personalized lesson system

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Create lesson_parts table
CREATE TABLE IF NOT EXISTS lesson_parts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lesson_id UUID NOT NULL REFERENCES "Lessons"(session_id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    part_order INTEGER NOT NULL,
    is_completed BOOLEAN NOT NULL DEFAULT FALSE,
    completed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 2. Create exercises table
CREATE TABLE IF NOT EXISTS exercises (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lesson_part_id UUID NOT NULL REFERENCES lesson_parts(id) ON DELETE CASCADE,
    exercise_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    instructions TEXT,
    correct_answer TEXT,
    explanation TEXT,
    difficulty_level VARCHAR(20) NOT NULL DEFAULT 'medium',
    exercise_order INTEGER NOT NULL,
    is_completed BOOLEAN NOT NULL DEFAULT FALSE,
    completed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 3. Create subtasks table
CREATE TABLE IF NOT EXISTS subtasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    exercise_id UUID NOT NULL REFERENCES exercises(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    subtask_type VARCHAR(50) NOT NULL,
    subtask_order INTEGER NOT NULL,
    is_optional BOOLEAN NOT NULL DEFAULT TRUE,
    is_completed BOOLEAN NOT NULL DEFAULT FALSE,
    completed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 4. Create lesson_part_progress table
CREATE TABLE IF NOT EXISTS lesson_part_progress (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lesson_part_id UUID NOT NULL REFERENCES lesson_parts(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'not_started',
    progress_percentage INTEGER NOT NULL DEFAULT 0,
    time_spent_minutes INTEGER NOT NULL DEFAULT 0,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(lesson_part_id, user_id)
);

-- 5. Create exercise_progress table
CREATE TABLE IF NOT EXISTS exercise_progress (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    exercise_id UUID NOT NULL REFERENCES exercises(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'not_started',
    attempts INTEGER NOT NULL DEFAULT 0,
    correct_attempts INTEGER NOT NULL DEFAULT 0,
    time_spent_minutes INTEGER NOT NULL DEFAULT 0,
    user_answer TEXT,
    is_correct BOOLEAN,
    feedback_received BOOLEAN NOT NULL DEFAULT FALSE,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(exercise_id, user_id)
);

-- 6. Create subtask_progress table
CREATE TABLE IF NOT EXISTS subtask_progress (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subtask_id UUID NOT NULL REFERENCES subtasks(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'not_started',
    time_spent_minutes INTEGER NOT NULL DEFAULT 0,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(subtask_id, user_id)
);

-- 7. Create lesson_extensions table
CREATE TABLE IF NOT EXISTS lesson_extensions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lesson_id UUID NOT NULL REFERENCES "Lessons"(session_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    extension_type VARCHAR(50) NOT NULL,
    parent_id UUID,
    extension_reason TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for optimal performance
CREATE INDEX IF NOT EXISTS ix_lesson_parts_lesson_id ON lesson_parts(lesson_id);
CREATE INDEX IF NOT EXISTS ix_lesson_parts_part_order ON lesson_parts(part_order);
CREATE INDEX IF NOT EXISTS ix_exercises_lesson_part_id ON exercises(lesson_part_id);
CREATE INDEX IF NOT EXISTS ix_exercises_exercise_order ON exercises(exercise_order);
CREATE INDEX IF NOT EXISTS ix_subtasks_exercise_id ON subtasks(exercise_id);
CREATE INDEX IF NOT EXISTS ix_subtasks_subtask_order ON subtasks(subtask_order);
CREATE INDEX IF NOT EXISTS ix_lesson_part_progress_lesson_part_id ON lesson_part_progress(lesson_part_id);
CREATE INDEX IF NOT EXISTS ix_lesson_part_progress_user_id ON lesson_part_progress(user_id);
CREATE INDEX IF NOT EXISTS ix_exercise_progress_exercise_id ON exercise_progress(exercise_id);
CREATE INDEX IF NOT EXISTS ix_exercise_progress_user_id ON exercise_progress(user_id);
CREATE INDEX IF NOT EXISTS ix_subtask_progress_subtask_id ON subtask_progress(subtask_id);
CREATE INDEX IF NOT EXISTS ix_subtask_progress_user_id ON subtask_progress(user_id);
CREATE INDEX IF NOT EXISTS ix_lesson_extensions_lesson_id ON lesson_extensions(lesson_id);
CREATE INDEX IF NOT EXISTS ix_lesson_extensions_user_id ON lesson_extensions(user_id);

-- Create composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS ix_lesson_parts_lesson_order ON lesson_parts(lesson_id, part_order);
CREATE INDEX IF NOT EXISTS ix_exercises_part_order ON exercises(lesson_part_id, exercise_order);
CREATE INDEX IF NOT EXISTS ix_subtasks_exercise_order ON subtasks(exercise_id, subtask_order);

-- Add constraints for data integrity
ALTER TABLE lesson_parts ADD CONSTRAINT chk_part_order_positive CHECK (part_order > 0);
ALTER TABLE exercises ADD CONSTRAINT chk_exercise_order_positive CHECK (exercise_order > 0);
ALTER TABLE subtasks ADD CONSTRAINT chk_subtask_order_positive CHECK (subtask_order > 0);
ALTER TABLE lesson_part_progress ADD CONSTRAINT chk_progress_percentage CHECK (progress_percentage >= 0 AND progress_percentage <= 100);
ALTER TABLE exercise_progress ADD CONSTRAINT chk_attempts_positive CHECK (attempts >= 0);
ALTER TABLE exercise_progress ADD CONSTRAINT chk_correct_attempts CHECK (correct_attempts <= attempts);

-- Create updated_at trigger function if it doesn't exist
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at columns
CREATE TRIGGER update_lesson_parts_updated_at BEFORE UPDATE ON lesson_parts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_exercises_updated_at BEFORE UPDATE ON exercises
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_subtasks_updated_at BEFORE UPDATE ON subtasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_lesson_part_progress_updated_at BEFORE UPDATE ON lesson_part_progress
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_exercise_progress_updated_at BEFORE UPDATE ON exercise_progress
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_subtask_progress_updated_at BEFORE UPDATE ON subtask_progress
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data for testing (optional)
-- Uncomment the following section if you want to insert sample data

/*
-- Sample lesson part
INSERT INTO lesson_parts (lesson_id, title, description, part_order) VALUES 
('00000000-0000-0000-0000-000000000001', 'Introduction to Forces', 'Learn the basics of forces', 1);

-- Sample exercise
INSERT INTO exercises (lesson_part_id, exercise_type, title, content, difficulty_level, exercise_order) VALUES 
('00000000-0000-0000-0000-000000000002', 'multiple_choice', 'What is force?', 'Which of the following best describes force?', 'easy', 1);

-- Sample subtask
INSERT INTO subtasks (exercise_id, title, content, subtask_type, subtask_order) VALUES 
('00000000-0000-0000-0000-000000000003', 'Additional Explanation', 'Force is a push or pull that can change motion', 'explanation', 1);
*/

-- Display table creation confirmation
SELECT 'Personalized lesson structure tables created successfully!' as status;

-- Show created tables
SELECT table_name, table_type 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('lesson_parts', 'exercises', 'subtasks', 'lesson_part_progress', 'exercise_progress', 'subtask_progress', 'lesson_extensions')
ORDER BY table_name;
