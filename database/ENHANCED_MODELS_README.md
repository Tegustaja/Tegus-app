# Enhanced Database Models for Tegus Education App

## Overview

This document describes the enhanced database models that support personalized learning with multiple subtasks, knowledge validation exercises, and comprehensive progress tracking. The system is designed to be extensible and support AI-generated adaptive lesson plans.

## Core Architecture

The enhanced system follows a hierarchical structure:
```
Subject → Topic → Subtask → Exercise
```

Each level can have multiple instances, and the system tracks student progress at every level.

## New Models

### 1. Subtask Model

**Purpose**: Represents individual learning activities within a topic that can be descriptive, explanatory, or exercise-based.

**Key Features**:
- **Flexible Types**: Supports descriptive content, explanations, exercises, quizzes, and interactive elements
- **Adaptive Learning**: Difficulty can adjust based on student performance
- **Prerequisites**: Can define dependencies between subtasks
- **Learning Objectives**: Clear goals for each subtask

**Fields**:
```python
class Subtask(Base):
    id = Column(UUID, primary_key=True)
    topic_id = Column(String, ForeignKey('topics.id'))
    title = Column(String(255))
    description = Column(Text)
    content = Column(Text)  # For descriptive/explanation content
    subtask_type = Column(Enum(SubtaskType))
    exercise_type = Column(Enum(ExerciseType))  # Only for exercise subtasks
    
    # Learning parameters
    difficulty_level = Column(Enum(DifficultyLevel))
    estimated_duration_minutes = Column(Integer)
    prerequisites = Column(JSON)  # List of prerequisite subtask IDs
    learning_objectives = Column(JSON)  # List of learning objectives
    
    # Organization
    subtask_order = Column(Integer)
    is_optional = Column(Boolean)
    is_adaptive = Column(Boolean)
```

### 2. Exercise Model

**Purpose**: Represents specific exercises within subtasks for knowledge validation and assessment.

**Key Features**:
- **Multiple Exercise Types**: Multiple choice, true/false, fill-in-blank, matching, calculations, essays, coding
- **Adaptive Difficulty**: Can adjust based on student performance
- **Rich Content**: Supports various answer formats and explanations
- **Scoring System**: Configurable points and success thresholds

**Fields**:
```python
class Exercise(Base):
    id = Column(UUID, primary_key=True)
    subtask_id = Column(UUID, ForeignKey('subtasks.id'))
    title = Column(String(255))
    question = Column(Text)
    exercise_type = Column(Enum(ExerciseType))
    
    # Content (varies by type)
    options = Column(JSON)  # For multiple choice, matching, etc.
    correct_answer = Column(Text)  # For single correct answers
    correct_answers = Column(JSON)  # For multiple correct answers
    explanation = Column(Text)  # Explanation of the correct answer
    
    # Difficulty and scoring
    difficulty_level = Column(Enum(DifficultyLevel))
    points = Column(Integer)
    time_limit_seconds = Column(Integer)
    success_threshold = Column(Float)
    adaptive_difficulty = Column(Boolean)
```

### 3. StudentSubtaskProgress Model

**Purpose**: Tracks detailed student progress through individual subtasks with performance metrics.

**Key Features**:
- **Comprehensive Tracking**: Progress percentage, time spent, attempts, scores
- **Performance Metrics**: Best score, average score, mastery level
- **Adaptive Data**: Current difficulty level and mastery progression
- **Status Management**: Not started, in progress, completed, or skipped

**Fields**:
```python
class StudentSubtaskProgress(Base):
    student_id = Column(UUID, ForeignKey('profiles.id'), primary_key=True)
    subtask_id = Column(UUID, ForeignKey('subtasks.id'), primary_key=True)
    
    # Progress tracking
    status = Column(Enum(ProgressStatus))
    progress_percentage = Column(Float)  # 0-100
    time_spent_minutes = Column(Integer)
    
    # Performance metrics
    attempts_count = Column(Integer)
    successful_attempts = Column(Integer)
    best_score = Column(Float)
    average_score = Column(Float)
    
    # Adaptive learning data
    current_difficulty = Column(Enum(DifficultyLevel))
    mastery_level = Column(Float)  # 0-1 scale
    
    # Timestamps
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    last_accessed = Column(DateTime)
```

### 4. StudentExerciseAttempt Model

**Purpose**: Records individual attempts at exercises for detailed performance analysis.

**Key Features**:
- **Attempt Tracking**: Complete history of student attempts
- **Performance Metrics**: Response time, hints used, confidence levels
- **Feedback System**: Stores feedback received and perceived difficulty
- **Learning Analytics**: Supports detailed analysis of learning patterns

**Fields**:
```python
class StudentExerciseAttempt(Base):
    id = Column(UUID, primary_key=True)
    student_id = Column(UUID, ForeignKey('profiles.id'))
    exercise_id = Column(UUID, ForeignKey('exercises.id'))
    lesson_id = Column(UUID, ForeignKey('Lessons.session_id'))
    
    # Attempt details
    answer = Column(Text)
    answers = Column(JSON)  # For multiple answers
    is_correct = Column(Boolean)
    score = Column(Float)  # 0-1 scale
    
    # Performance metrics
    response_time_seconds = Column(Float)
    hints_used = Column(Integer)
    attempts_before_success = Column(Integer)
    
    # Feedback and learning
    feedback_received = Column(Text)
    student_confidence = Column(Float)  # 0-1 scale
    difficulty_perceived = Column(Enum(DifficultyLevel))
```

### 5. AdaptiveLessonPlan Model

**Purpose**: Stores AI-generated personalized lesson plans that can adapt during learning.

**Key Features**:
- **AI-Generated Content**: Personalized subtask sequences and difficulty progressions
- **Dynamic Adaptation**: Can be modified during the lesson based on performance
- **Learning Objectives**: Clear goals and estimated durations
- **Expiration Management**: Plans can become stale and need regeneration

**Fields**:
```python
class AdaptiveLessonPlan(Base):
    id = Column(UUID, primary_key=True)
    student_id = Column(UUID, ForeignKey('profiles.id'))
    topic_id = Column(String, ForeignKey('topics.id'))
    lesson_id = Column(UUID, ForeignKey('Lessons.session_id'))
    
    # Lesson plan details
    title = Column(String(255))
    description = Column(Text)
    learning_objectives = Column(JSON)
    estimated_duration_minutes = Column(Integer)
    
    # AI-generated content
    subtask_sequence = Column(JSON)  # Ordered list of subtask IDs
    difficulty_progression = Column(JSON)  # Difficulty changes throughout lesson
    adaptive_parameters = Column(JSON)  # AI parameters for personalization
    
    # Progress tracking
    current_subtask_index = Column(Integer)
    is_completed = Column(Boolean)
    completion_percentage = Column(Float)
    
    # Metadata
    expires_at = Column(DateTime)  # When the plan becomes stale
```

### 6. LearningAnalytics Model

**Purpose**: Stores comprehensive learning analytics for insights and system improvement.

**Key Features**:
- **Session Tracking**: Complete learning session data with timing
- **Performance Metrics**: Accuracy rates, completion rates, engagement scores
- **Behavioral Analysis**: Time per exercise, hints usage, focus patterns
- **Engagement Metrics**: Focus time, breaks taken, overall engagement

**Fields**:
```python
class LearningAnalytics(Base):
    id = Column(UUID, primary_key=True)
    student_id = Column(UUID, ForeignKey('profiles.id'))
    topic_id = Column(String, ForeignKey('topics.id'))
    subtask_id = Column(UUID, ForeignKey('subtasks.id'))
    
    # Learning session data
    session_start = Column(DateTime)
    session_end = Column(DateTime)
    session_duration_minutes = Column(Integer)
    
    # Performance metrics
    exercises_attempted = Column(Integer)
    exercises_completed = Column(Integer)
    correct_answers = Column(Integer)
    accuracy_rate = Column(Float)
    
    # Learning behavior
    time_per_exercise = Column(Float)
    hints_used_total = Column(Integer)
    skipped_exercises = Column(Integer)
    
    # Engagement metrics
    engagement_score = Column(Float)  # 0-1 scale
    focus_time_minutes = Column(Integer)
    breaks_taken = Column(Integer)
```

## Enhanced Existing Models

### Profile Model Enhancements

Added learning preferences and adaptive learning settings:
```python
# Enhanced learning preferences
learning_style = Column(String(50))  # 'visual', 'auditory', 'kinesthetic', 'reading'
preferred_difficulty = Column(Enum(DifficultyLevel))
adaptive_learning_enabled = Column(Boolean, default=True)
progress_report_frequency = Column(String(20), default='weekly')
```

### Topic Model Enhancements

Added adaptive learning capabilities:
```python
# Enhanced fields for adaptive learning
difficulty_curve = Column(JSON)  # Difficulty progression through subtasks
prerequisites = Column(JSON)  # List of prerequisite topic IDs
learning_path = Column(JSON)  # Suggested learning sequence
```

## Enums and Constants

### SubtaskType
- `DESCRIPTIVE`: Static content for reading/learning
- `EXPLANATION`: Detailed explanations of concepts
- `EXERCISE`: Interactive exercises for practice
- `QUIZ`: Assessment questions
- `INTERACTIVE`: Dynamic, adaptive content

### ExerciseType
- `MULTIPLE_CHOICE`: Multiple choice questions
- `TRUE_FALSE`: True/false questions
- `FILL_BLANK`: Fill-in-the-blank exercises
- `MATCHING`: Matching exercises
- `CALCULATION`: Mathematical calculations
- `ESSAY`: Written responses
- `CODING`: Programming exercises

### DifficultyLevel
- `BEGINNER`: Introductory level content
- `INTERMEDIATE`: Standard difficulty
- `ADVANCED`: Challenging content

### ProgressStatus
- `NOT_STARTED`: Student hasn't begun
- `IN_PROGRESS`: Currently working on
- `COMPLETED`: Successfully finished
- `SKIPPED`: Intentionally bypassed

## Database Indexes

The system includes comprehensive indexing for optimal performance:
- Foreign key relationships
- Frequently queried fields (status, difficulty, timestamps)
- Composite indexes for multi-field queries
- Performance-critical fields (student_id, topic_id, etc.)

## Usage Examples

### Creating a Learning Path

```python
# Create a topic with subtasks
topic = Topic(
    id="physics_mechanics",
    name="Classical Mechanics",
    subject_id="physics"
)

# Add descriptive subtask
descriptive_subtask = Subtask(
    topic_id="physics_mechanics",
    title="Introduction to Forces",
    subtask_type=SubtaskType.DESCRIPTIVE,
    content="Forces are interactions that can change motion...",
    subtask_order=1
)

# Add exercise subtask
exercise_subtask = Subtask(
    topic_id="physics_mechanics",
    title="Force Calculation Practice",
    subtask_type=SubtaskType.EXERCISE,
    exercise_type=ExerciseType.CALCULATION,
    subtask_order=2
)

# Add exercise to subtask
exercise = Exercise(
    subtask_id=exercise_subtask.id,
    title="Calculate Net Force",
    question="A 5N force acts east and a 3N force acts west. What's the net force?",
    exercise_type=ExerciseType.CALCULATION,
    correct_answer="2N east",
    difficulty_level=DifficultyLevel.BEGINNER
)
```

### Tracking Student Progress

```python
# Record student progress
progress = StudentSubtaskProgress(
    student_id=student.id,
    subtask_id=subtask.id,
    status=ProgressStatus.IN_PROGRESS,
    progress_percentage=75.0,
    time_spent_minutes=12
)

# Record exercise attempt
attempt = StudentExerciseAttempt(
    student_id=student.id,
    exercise_id=exercise.id,
    answer="2N east",
    is_correct=True,
    score=1.0,
    response_time_seconds=45.2,
    student_confidence=0.9
)
```

### Creating Adaptive Lesson Plans

```python
# AI-generated lesson plan
lesson_plan = AdaptiveLessonPlan(
    student_id=student.id,
    topic_id="physics_mechanics",
    title="Personalized Mechanics Journey",
    learning_objectives=["Understand forces", "Solve basic problems"],
    subtask_sequence=[str(subtask1.id), str(subtask2.id), str(subtask3.id)],
    difficulty_progression=["beginner", "intermediate", "advanced"],
    adaptive_parameters={
        "learning_rate": 0.1,
        "difficulty_adjustment": 0.2,
        "mastery_threshold": 0.8
    }
)
```

## Testing

Run the comprehensive test suite to verify all models work correctly:

```bash
cd tests
python3 test_database_models.py
```

The test suite covers:
- Model creation and validation
- Relationship integrity
- Enum value validation
- Database operations
- Performance testing

## Migration Notes

When upgrading existing databases:

1. **New Tables**: The new models create additional tables that don't affect existing data
2. **Enhanced Fields**: Existing models get new optional fields with sensible defaults
3. **Indexes**: New performance indexes are added automatically
4. **Backward Compatibility**: All existing functionality remains intact

## Future Enhancements

The system is designed to support:
- **Real-time Adaptation**: Dynamic difficulty adjustment during lessons
- **AI Integration**: Machine learning for personalized content generation
- **Advanced Analytics**: Predictive modeling and learning path optimization
- **Multi-modal Content**: Support for video, audio, and interactive media
- **Collaborative Learning**: Group exercises and peer assessment
- **Gamification**: Points, badges, and achievement systems

## Support

For questions or issues with the enhanced database models, refer to:
- Database schema documentation
- API endpoint documentation
- Test suite examples
- Migration guides
