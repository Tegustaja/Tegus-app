# Personalized Lesson Structure Database Models

This document describes the database models for the personalized lesson structure in the Tegus education app. The system supports creating unique, personalized lessons for each student with the ability to extend content during learning.

## Overview

The personalized lesson structure follows this hierarchy:
```
Lesson
  |-- LessonPart 1
    |-- Exercise 1 (Some kind of exercise/explanation)
    |-- Exercise 2
       |-- Subtask 1 (Optional, may not be present under all exercises)
       |-- Subtask 2 (There may be multiple subtasks)
    |-- Exercise 3
    |-- Exercise 4
  |-- LessonPart 2
  ...
```

## Key Features

- **Personalization**: Each lesson is unique to a student and cannot be shared
- **Extensibility**: Lessons, lesson parts, exercises, and subtasks can be extended during learning
- **Progress Tracking**: Comprehensive progress tracking at every level
- **Flexible Exercise Types**: Support for multiple choice, true/false, calculations, explanations, and interactive content
- **Optional Subtasks**: Subtasks are optional and can be added dynamically

## Database Models

### Core Models

#### 1. Lesson
The main lesson entity that represents a personalized learning session.

**Table**: `Lessons`
**Key Fields**:
- `session_id` (UUID, Primary Key): Unique session identifier
- `user_id` (UUID): Reference to the student's profile
- `topic_id` (String): Reference to the subject topic
- `title` (Text): Lesson title
- `focus_area` (Text): Specific area of focus
- `proficiency_level` (Text): Student's proficiency level
- `is_completed` (Boolean): Whether the lesson is completed

**Relationships**:
- Has many `LessonPart`s
- Has many `SessionMessage`s
- Belongs to one `Profile`

#### 2. LessonPart
Individual parts within a lesson, organized in sequence.

**Table**: `lesson_parts`
**Key Fields**:
- `id` (UUID, Primary Key): Unique identifier
- `lesson_id` (UUID): Reference to the parent lesson
- `title` (String): Part title
- `description` (Text): Part description
- `part_order` (Integer): Order within the lesson
- `is_completed` (Boolean): Whether the part is completed

**Relationships**:
- Has many `Exercise`s
- Has one `LessonPartProgress`
- Belongs to one `Lesson`

#### 3. Exercise
Different types of exercises within lesson parts.

**Table**: `exercises`
**Key Fields**:
- `id` (UUID, Primary Key): Unique identifier
- `lesson_part_id` (UUID): Reference to the parent lesson part
- `exercise_type` (String): Type of exercise ('multiple_choice', 'true_false', 'calculation', 'explanation', 'interactive')
- `title` (String): Exercise title
- `content` (Text): Exercise content/questions
- `correct_answer` (Text): Correct answer (if applicable)
- `explanation` (Text): Explanation of the answer
- `difficulty_level` (String): 'easy', 'medium', 'hard'
- `exercise_order` (Integer): Order within the lesson part

**Relationships**:
- Has many `Subtask`s
- Has one `ExerciseProgress`
- Belongs to one `LessonPart`

#### 4. Subtask
Optional subtasks under exercises that can be extended during learning.

**Table**: `subtasks`
**Key Fields**:
- `id` (UUID, Primary Key): Unique identifier
- `exercise_id` (UUID): Reference to the parent exercise
- `title` (String): Subtask title
- `content` (Text): Subtask content
- `subtask_type` (String): Type of subtask ('explanation', 'practice', 'reinforcement', 'extension')
- `subtask_order` (Integer): Order within the exercise
- `is_optional` (Boolean): Whether this subtask is required

**Relationships**:
- Has one `SubtaskProgress`
- Belongs to one `Exercise`

### Progress Tracking Models

#### 5. LessonPartProgress
Tracks progress for individual lesson parts.

**Table**: `lesson_part_progress`
**Key Fields**:
- `id` (UUID, Primary Key): Unique identifier
- `lesson_part_id` (UUID): Reference to the lesson part
- `user_id` (UUID): Reference to the student
- `status` (String): 'not_started', 'in_progress', 'completed'
- `progress_percentage` (Integer): 0-100 progress
- `time_spent_minutes` (Integer): Time spent on this part

#### 6. ExerciseProgress
Tracks progress for individual exercises.

**Table**: `exercise_progress`
**Key Fields**:
- `id` (UUID, Primary Key): Unique identifier
- `exercise_id` (UUID): Reference to the exercise
- `user_id` (UUID): Reference to the student
- `status` (String): 'not_started', 'in_progress', 'completed', 'failed'
- `attempts` (Integer): Number of attempts
- `correct_attempts` (Integer): Number of correct attempts
- `user_answer` (Text): Student's answer
- `is_correct` (Boolean): Whether the answer was correct

#### 7. SubtaskProgress
Tracks progress for individual subtasks.

**Table**: `subtask_progress`
**Key Fields**:
- `id` (UUID, Primary Key): Unique identifier
- `subtask_id` (UUID): Reference to the subtask
- `user_id` (UUID): Reference to the student
- `status` (String): 'not_started', 'in_progress', 'completed'
- `time_spent_minutes` (Integer): Time spent on this subtask

### Extension Tracking

#### 8. LessonExtension
Tracks when lessons are extended during learning.

**Table**: `lesson_extensions`
**Key Fields**:
- `id` (UUID, Primary Key): Unique identifier
- `lesson_id` (UUID): Reference to the lesson
- `user_id` (UUID): Reference to the student
- `extension_type` (String): 'lesson_part', 'exercise', 'subtask'
- `parent_id` (UUID): ID of the parent component being extended
- `extension_reason` (Text): Why the extension was requested

## Database Schema

### Table Relationships
```
profiles (1) ←→ (many) Lessons
Lessons (1) ←→ (many) lesson_parts
lesson_parts (1) ←→ (many) exercises
exercises (1) ←→ (many) subtasks

profiles (1) ←→ (many) lesson_part_progress
profiles (1) ←→ (many) exercise_progress
profiles (1) ←→ (many) subtask_progress
profiles (1) ←→ (many) lesson_extensions
```

### Indexes
The following indexes are created for optimal performance:
- `ix_lesson_parts_lesson_id`: For fast lesson part lookups
- `ix_lesson_parts_part_order`: For ordered lesson part retrieval
- `ix_exercises_lesson_part_id`: For fast exercise lookups
- `ix_exercises_exercise_order`: For ordered exercise retrieval
- `ix_subtasks_exercise_id`: For fast subtask lookups
- `ix_subtasks_subtask_order`: For ordered subtask retrieval
- Progress tracking indexes for user_id and component_id combinations

## Usage Examples

### Creating a New Lesson Structure

```python
from database.models import Lesson, LessonPart, Exercise, Subtask

# Create a lesson
lesson = Lesson(
    user_id=student_id,
    topic_id="physics_mechanics",
    title="Introduction to Forces",
    focus_area="Basic force concepts",
    proficiency_level="beginner"
)

# Create lesson parts
part1 = LessonPart(
    lesson_id=lesson.session_id,
    title="Understanding Force",
    description="Learn what force is and how it affects motion",
    part_order=1
)

# Create exercises
exercise1 = Exercise(
    lesson_part_id=part1.id,
    exercise_type="multiple_choice",
    title="What is force?",
    content="Which of the following best describes force?",
    difficulty_level="easy",
    exercise_order=1
)

# Create optional subtasks
subtask1 = Subtask(
    exercise_id=exercise1.id,
    title="Additional Explanation",
    content="Force is a push or pull that can change motion",
    subtask_type="explanation",
    subtask_order=1
)
```

### Extending a Lesson During Learning

```python
from database.models import LessonExtension, Exercise

# Record the extension request
extension = LessonExtension(
    lesson_id=lesson.session_id,
    user_id=student_id,
    extension_type="exercise",
    parent_id=exercise1.id,
    extension_reason="Student needs more practice with force concepts"
)

# Create the new exercise
new_exercise = Exercise(
    lesson_part_id=part1.id,
    exercise_type="calculation",
    title="Force Calculation Practice",
    content="Calculate the net force on an object...",
    difficulty_level="medium",
    exercise_order=2  # Insert after the first exercise
)
```

### Tracking Progress

```python
from database.models import ExerciseProgress

# Record exercise completion
progress = ExerciseProgress(
    exercise_id=exercise1.id,
    user_id=student_id,
    status="completed",
    attempts=2,
    correct_attempts=1,
    user_answer="A push or pull",
    is_correct=True,
    time_spent_minutes=5
)
```

## Migration Considerations

When implementing these models:

1. **Database Migration**: Use Alembic to create the new tables
2. **Data Migration**: Consider migrating existing lesson data to the new structure
3. **Backward Compatibility**: Ensure existing code continues to work during transition
4. **Performance**: Monitor query performance with the new structure

## Testing

A comprehensive test suite is available in `tests/test_models.py` that verifies:
- Model imports
- Model instantiation
- Relationship definitions
- Table name definitions

Run the tests with:
```bash
python3 tests/test_models.py
```

## Future Enhancements

Potential improvements to consider:
- **Content Versioning**: Track different versions of exercises and subtasks
- **Collaborative Learning**: Allow students to share successful lesson extensions
- **AI-Generated Content**: Automatically generate additional exercises based on student performance
- **Learning Analytics**: Enhanced progress tracking and analytics
- **Content Templates**: Reusable templates for common exercise types

## Conclusion

This database structure provides a flexible foundation for personalized learning experiences. The hierarchical organization allows for natural lesson flow while the extensibility features support adaptive learning based on student needs. The comprehensive progress tracking enables detailed analytics and personalized recommendations.
