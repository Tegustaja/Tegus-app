from sqlalchemy import Column, Integer, String, Text, DateTime, Date, ForeignKey, Index, BigInteger, JSON, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

Base = declarative_base()

class Profile(Base):
    __tablename__ = "profiles"
    
    # Essential fields only
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, index=True)
    
    # Password security fields
    password_hash = Column(String(255), nullable=True)
    salt = Column(String(255), nullable=True)
    
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    
    # Basic account status
    email_verified = Column(Boolean, default=True, nullable=False)
    account_status = Column(String(20), default='active', nullable=False)
    
    # Admin privileges
    is_admin = Column(Boolean, default=False, nullable=False)
    admin_expires_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    onboarding_data = relationship("OnboardingData", back_populates="profile", uselist=False)
    user_statistics = relationship("UserStatistics", back_populates="profile", uselist=False)
    user_streaks = relationship("UserStreaks", back_populates="profile", uselist=False)
    lessons = relationship("Lesson", back_populates="profile")
    user_progress = relationship("UserProgress", back_populates="profile")
    topic_states = relationship("StudentTopicState", back_populates="profile")

class OnboardingData(Base):
    __tablename__ = 'onboarding_data'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id'))
    heard_from = Column(String)
    learning_reason = Column(String)
    daily_goal = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    profile = relationship("Profile", back_populates="onboarding_data")

class UserStatistics(Base):
    __tablename__ = 'user_statistics'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id'))
    total_lessons = Column(Integer, default=0)
    total_study_time_minutes = Column(Integer, default=0)
    total_tests_completed = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    profile = relationship("Profile", back_populates="user_statistics")

class UserStreaks(Base):
    __tablename__ = 'user_streaks'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id'))
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    last_study_date = Column(Date)
    points = Column(Integer, default=0)
    hearts = Column(Integer, default=5)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    profile = relationship("Profile", back_populates="user_streaks")

class Prompt(Base):
    __tablename__ = 'prompts'
    
    id = Column(Integer, primary_key=True)
    user = Column(String)
    prompt = Column(Text)
    response = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class Subject(Base):
    __tablename__ = 'subjects'
    
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    color = Column(String, nullable=False)
    icon = Column(String, nullable=False)
    is_unlocked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    topics = relationship("Topic", back_populates="subject")

class Topic(Base):
    __tablename__ = 'topics'
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    subject_id = Column(String, ForeignKey('subjects.id'), nullable=False)
    topic_order = Column(Integer, nullable=False)
    is_locked = Column(Boolean, default=True)
    icon = Column(String, nullable=False)
    position = Column(String, nullable=False)  # 'left', 'center', 'right'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    subject = relationship("Subject", back_populates="topics")

class Lesson(Base):
    __tablename__ = 'Lessons'
    
    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id'))
    topic_id = Column(String)
    title = Column(Text)
    focus_area = Column(Text)
    proficiency_level = Column(Text)
    steps = Column(JSON)  # JSONB equivalent
    step_statuses = Column(JSON)
    step_responses = Column(JSON)
    steps_feedback = Column(JSON)
    start_time = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)
    current_database_index = Column(BigInteger)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    profile = relationship("Profile", back_populates="lessons")
    messages = relationship("SessionMessage", back_populates="lesson")
    lesson_parts = relationship("LessonPart", back_populates="lesson", order_by="LessonPart.part_order")

class SessionMessage(Base):
    __tablename__ = 'session_messages'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('Lessons.session_id'), nullable=False)
    role = Column(String, nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    lesson = relationship("Lesson", back_populates="messages")

class UserProgress(Base):
    __tablename__ = 'user_progress'
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id'), primary_key=True)
    topic_id = Column(String, ForeignKey('topics.id'), primary_key=True)
    progress = Column(Integer, nullable=False)  # 0-100
    last_accessed = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    profile = relationship("Profile", back_populates="user_progress")
    topic = relationship("Topic")

class StudentTopicState(Base):
    """Tracks adaptive learning metrics for each student-topic combination"""
    __tablename__ = 'student_topic_state'
    
    student_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id'), primary_key=True)
    topic_id = Column(String, ForeignKey('topics.id'), primary_key=True)
    
    # Core metrics (0-1 scale)
    mastery = Column(Float, default=0.0, nullable=False)
    correct_ema = Column(Float, default=0.0, nullable=False)  # Exponential moving average of correctness
    volatility = Column(Float, default=0.5, nullable=False)   # Higher = less stable
    pace = Column(Float, default=0.5, nullable=False)         # Speed relative to target
    calibration = Column(Float, default=0.5, nullable=False)  # Confidence vs correctness alignment
    
    # Computed metrics
    learning_index = Column(Integer, default=0, nullable=False)  # 0-100 overall score
    difficulty_band = Column(String, default='intro', nullable=False)  # intro/core/stretch
    
    # Metadata
    last_seen_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    profile = relationship("Profile", back_populates="topic_states")
    topic = relationship("Topic")

class DiagnosticEvent(Base):
    """Stores diagnostic and learning interaction events"""
    __tablename__ = 'diagnostic_events'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id'), nullable=False)
    subject_id = Column(String, ForeignKey('subjects.id'), nullable=False)
    topic_id = Column(String, ForeignKey('topics.id'), nullable=False)
    
    # Event details
    event_type = Column(String, nullable=False)  # 'probe', 'exercise', 'explain'
    correct = Column(Boolean, nullable=False)
    latency_ms = Column(Integer, nullable=False)  # Response time in milliseconds
    confidence = Column(Float)  # Student's self-reported confidence (0-1)
    
    # Additional metadata
    item_id = Column(String)  # ID of the specific probe/exercise item
    difficulty = Column(String)  # 'easy', 'medium', 'hard'
    result_metadata = Column(JSON)  # Additional result data
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    profile = relationship("Profile")
    subject = relationship("Subject")
    topic = relationship("Topic")

# New models for personalized lesson structure
class LessonPart(Base):
    """Represents individual parts within a lesson"""
    __tablename__ = 'lesson_parts'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lesson_id = Column(UUID(as_uuid=True), ForeignKey('Lessons.session_id'), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    part_order = Column(Integer, nullable=False)  # Order within the lesson
    is_completed = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    lesson = relationship("Lesson", back_populates="lesson_parts")
    exercises = relationship("Exercise", back_populates="lesson_part", order_by="Exercise.exercise_order")
    progress = relationship("LessonPartProgress", back_populates="lesson_part", uselist=False)

class Exercise(Base):
    """Represents exercises within lesson parts"""
    __tablename__ = 'exercises'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lesson_part_id = Column(UUID(as_uuid=True), ForeignKey('lesson_parts.id'), nullable=False)
    exercise_type = Column(String(50), nullable=False)  # 'multiple_choice', 'true_false', 'calculation', 'explanation', 'interactive'
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)  # Exercise content/questions
    instructions = Column(Text, nullable=True)
    correct_answer = Column(Text, nullable=True)  # For exercises with correct answers
    explanation = Column(Text, nullable=True)  # Explanation of the answer
    difficulty_level = Column(String(20), default='medium', nullable=False)  # 'easy', 'medium', 'hard'
    exercise_order = Column(Integer, nullable=False)  # Order within the lesson part
    is_completed = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    lesson_part = relationship("LessonPart", back_populates="exercises")
    subtasks = relationship("Subtask", back_populates="exercise", order_by="Subtask.subtask_order")
    progress = relationship("ExerciseProgress", back_populates="exercise", uselist=False)

class Subtask(Base):
    """Optional subtasks under exercises that can be extended during learning"""
    __tablename__ = 'subtasks'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exercise_id = Column(UUID(as_uuid=True), ForeignKey('exercises.id'), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    subtask_type = Column(String(50), nullable=False)  # 'explanation', 'practice', 'reinforcement', 'extension'
    subtask_order = Column(Integer, nullable=False)  # Order within the exercise
    is_optional = Column(Boolean, default=True, nullable=False)  # Whether this subtask is required
    is_completed = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    exercise = relationship("Exercise", back_populates="subtasks")
    progress = relationship("SubtaskProgress", back_populates="subtask", uselist=False)

class LessonPartProgress(Base):
    """Tracks progress for individual lesson parts"""
    __tablename__ = 'lesson_part_progress'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lesson_part_id = Column(UUID(as_uuid=True), ForeignKey('lesson_parts.id'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id'), nullable=False)
    status = Column(String(20), default='not_started', nullable=False)  # 'not_started', 'in_progress', 'completed'
    progress_percentage = Column(Integer, default=0, nullable=False)  # 0-100
    time_spent_minutes = Column(Integer, default=0, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    lesson_part = relationship("LessonPart", back_populates="progress")
    profile = relationship("Profile")

class ExerciseProgress(Base):
    """Tracks progress for individual exercises"""
    __tablename__ = 'exercise_progress'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exercise_id = Column(UUID(as_uuid=True), ForeignKey('exercises.id'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id'), nullable=False)
    status = Column(String(20), default='not_started', nullable=False)  # 'not_started', 'in_progress', 'completed', 'failed'
    attempts = Column(Integer, default=0, nullable=False)
    correct_attempts = Column(Integer, default=0, nullable=False)
    time_spent_minutes = Column(Integer, default=0, nullable=False)
    user_answer = Column(Text, nullable=True)  # Student's answer
    is_correct = Column(Boolean, nullable=True)  # Whether the answer was correct
    feedback_received = Column(Boolean, default=False, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    exercise = relationship("Exercise", back_populates="progress")
    profile = relationship("Profile")

class SubtaskProgress(Base):
    """Tracks progress for individual subtasks"""
    __tablename__ = 'subtask_progress'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subtask_id = Column(UUID(as_uuid=True), ForeignKey('subtasks.id'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id'), nullable=False)
    status = Column(String(20), default='not_started', nullable=False)  # 'not_started', 'in_progress', 'completed'
    time_spent_minutes = Column(Integer, default=0, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    subtask = relationship("Subtask", back_populates="progress")
    profile = relationship("Profile")

class LessonExtension(Base):
    """Tracks when lessons are extended during learning"""
    __tablename__ = 'lesson_extensions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lesson_id = Column(UUID(as_uuid=True), ForeignKey('Lessons.session_id'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id'), nullable=False)
    extension_type = Column(String(50), nullable=False)  # 'lesson_part', 'exercise', 'subtask'
    parent_id = Column(UUID(as_uuid=True), nullable=True)  # ID of the parent component being extended
    extension_reason = Column(Text, nullable=True)  # Why the extension was requested
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    lesson = relationship("Lesson")
    profile = relationship("Profile")

# Create indexes
Index('ix_onboarding_data_user_id', OnboardingData.user_id)
Index('ix_user_statistics_user_id', UserStatistics.user_id)
Index('ix_user_streaks_user_id', UserStreaks.user_id)
Index('ix_lessons_user_id', Lesson.user_id)
Index('ix_lessons_session_id', Lesson.session_id)
Index('ix_topics_subject_id', Topic.subject_id)
Index('ix_topics_topic_order', Topic.topic_order)
Index('ix_session_messages_session_id', SessionMessage.session_id)
Index('ix_user_progress_user_id', UserProgress.user_id)
Index('ix_user_progress_topic_id', UserProgress.topic_id)
Index('ix_profiles_is_admin', Profile.is_admin)
Index('ix_profiles_admin_expires_at', Profile.admin_expires_at)

# Adaptive learning indexes
Index('ix_student_topic_state_student_id', StudentTopicState.student_id)
Index('ix_student_topic_state_topic_id', StudentTopicState.topic_id)
Index('ix_diagnostic_events_student_id', DiagnosticEvent.student_id)
Index('ix_diagnostic_events_topic_id', DiagnosticEvent.topic_id)
Index('ix_diagnostic_events_created_at', DiagnosticEvent.created_at)

# New model indexes
Index('ix_lesson_parts_lesson_id', LessonPart.lesson_id)
Index('ix_lesson_parts_part_order', LessonPart.part_order)
Index('ix_exercises_lesson_part_id', Exercise.lesson_part_id)
Index('ix_exercises_exercise_order', Exercise.exercise_order)
Index('ix_subtasks_exercise_id', Subtask.exercise_id)
Index('ix_subtasks_subtask_order', Subtask.subtask_order)
Index('ix_lesson_part_progress_lesson_part_id', LessonPartProgress.lesson_part_id)
Index('ix_lesson_part_progress_user_id', LessonPartProgress.user_id)
Index('ix_exercise_progress_exercise_id', ExerciseProgress.exercise_id)
Index('ix_exercise_progress_user_id', ExerciseProgress.user_id)
Index('ix_subtask_progress_subtask_id', SubtaskProgress.subtask_id)
Index('ix_subtask_progress_user_id', SubtaskProgress.user_id)
Index('ix_lesson_extensions_lesson_id', LessonExtension.lesson_id)
Index('ix_lesson_extensions_user_id', LessonExtension.user_id)
