from sqlalchemy import Column, Integer, String, Text, DateTime, Date, ForeignKey, Index, BigInteger, JSON, Boolean, Float, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
import enum

Base = declarative_base()

# Enums for better type safety
class SubtaskType(enum.Enum):
    DESCRIPTIVE = "descriptive"
    EXPLANATION = "explanation"
    EXERCISE = "exercise"
    QUIZ = "quiz"
    INTERACTIVE = "interactive"

class ExerciseType(enum.Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    FILL_BLANK = "fill_blank"
    MATCHING = "matching"
    CALCULATION = "calculation"
    ESSAY = "essay"
    CODING = "coding"

class DifficultyLevel(enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class ProgressStatus(enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"

class Profile(Base):
    __tablename__ = 'profiles'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, index=True)  # Allow duplicates for learning purposes
    password_hash = Column(String(255), nullable=True)  # For local authentication
    salt = Column(String(255), nullable=True)  # For password hashing
    
    # Personal Information
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    display_name = Column(String(150), nullable=True, index=True)
    phone_number = Column(String(20), nullable=True, unique=True)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String(20), nullable=True)
    
    # Professional Information
    company = Column(String(150), nullable=True)
    job_title = Column(String(100), nullable=True)
    department = Column(String(100), nullable=True)
    years_of_experience = Column(Integer, nullable=True)
    
    # Educational Information
    education_level = Column(String(50), nullable=True)
    field_of_study = Column(String(100), nullable=True)
    institution = Column(String(150), nullable=True)
    graduation_year = Column(Integer, nullable=True)
    
    # Account & Security
    email_verified = Column(Boolean, default=False, nullable=False)
    phone_verified = Column(Boolean, default=False, nullable=False)
    two_factor_enabled = Column(Boolean, default=False, nullable=False)
    last_login_at = Column(DateTime, nullable=True, index=True)
    login_count = Column(Integer, default=0, nullable=False)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    account_locked_until = Column(DateTime, nullable=True)
    
    # Preferences & Settings
    timezone = Column(String(50), default='UTC', nullable=False)
    language = Column(String(10), default='en', nullable=False)
    theme = Column(String(20), default='light', nullable=False)
    notification_preferences = Column(JSON, nullable=True)
    
    # Social & Networking
    linkedin_url = Column(String(255), nullable=True)
    github_url = Column(String(255), nullable=True)
    twitter_url = Column(String(255), nullable=True)
    website_url = Column(String(255), nullable=True)
    
    # Privacy & Compliance
    privacy_level = Column(String(20), default='standard', nullable=False)
    gdpr_consent = Column(Boolean, default=False, nullable=False)
    marketing_consent = Column(Boolean, default=False, nullable=False)
    data_processing_consent = Column(Boolean, default=False, nullable=False)
    
    # Status & Verification
    account_status = Column(String(20), default='active', nullable=False, index=True)
    verification_token = Column(String(255), nullable=True)
    verification_expires_at = Column(DateTime, nullable=True)
    
    # Legacy fields
    avatar_url = Column(String)
    is_admin = Column(Boolean, default=False)
    admin_expires_at = Column(DateTime)  # When admin privileges expire
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Enhanced learning preferences
    learning_style = Column(String(50), nullable=True)  # 'visual', 'auditory', 'kinesthetic', 'reading'
    preferred_difficulty = Column(Enum(DifficultyLevel), default=DifficultyLevel.INTERMEDIATE)
    adaptive_learning_enabled = Column(Boolean, default=True)
    progress_report_frequency = Column(String(20), default='weekly')  # 'daily', 'weekly', 'monthly'
    
    # Relationships
    onboarding_data = relationship("OnboardingData", back_populates="profile", uselist=False)
    user_statistics = relationship("UserStatistics", back_populates="profile", uselist=False)
    user_streaks = relationship("UserStreaks", back_populates="profile", uselist=False)
    lessons = relationship("Lesson", back_populates="profile")
    user_progress = relationship("UserProgress", back_populates="profile")
    topic_states = relationship("StudentTopicState", back_populates="profile")
    subtask_progress = relationship("StudentSubtaskProgress", back_populates="profile")
    exercise_attempts = relationship("StudentExerciseAttempt", back_populates="profile")
    lesson_plans = relationship("AdaptiveLessonPlan", back_populates="profile")
    learning_analytics = relationship("LearningAnalytics", back_populates="profile")

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
    
    # Enhanced fields for adaptive learning
    difficulty_curve = Column(JSON, nullable=True)  # Difficulty progression through subtasks
    prerequisites = Column(JSON, nullable=True)  # List of prerequisite topic IDs
    learning_path = Column(JSON, nullable=True)  # Suggested learning sequence
    
    # Relationships
    subject = relationship("Subject", back_populates="topics")
    subtasks = relationship("Subtask", back_populates="topic", order_by="Subtask.subtask_order")

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

class Subtask(Base):
    """Represents individual learning activities within a topic"""
    __tablename__ = 'subtasks'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic_id = Column(String, ForeignKey('topics.id'), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=True)  # For descriptive/explanation content
    subtask_type = Column(Enum(SubtaskType), nullable=False)
    exercise_type = Column(Enum(ExerciseType), nullable=True)  # Only for exercise subtasks
    
    # Learning parameters
    difficulty_level = Column(Enum(DifficultyLevel), default=DifficultyLevel.INTERMEDIATE)
    estimated_duration_minutes = Column(Integer, default=10)
    prerequisites = Column(JSON, nullable=True)  # List of prerequisite subtask IDs
    learning_objectives = Column(JSON, nullable=True)  # List of learning objectives
    
    # Ordering and organization
    subtask_order = Column(Integer, nullable=False)
    is_optional = Column(Boolean, default=False)
    is_adaptive = Column(Boolean, default=True)  # Whether difficulty adjusts based on performance
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    topic = relationship("Topic", back_populates="subtasks")
    exercises = relationship("Exercise", back_populates="subtask")
    student_progress = relationship("StudentSubtaskProgress", back_populates="subtask")

class Exercise(Base):
    """Represents specific exercises within subtasks"""
    __tablename__ = 'exercises'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subtask_id = Column(UUID(as_uuid=True), ForeignKey('subtasks.id'), nullable=False)
    title = Column(String(255), nullable=False)
    question = Column(Text, nullable=False)
    exercise_type = Column(Enum(ExerciseType), nullable=False)
    
    # Exercise content (varies by type)
    options = Column(JSON, nullable=True)  # For multiple choice, matching, etc.
    correct_answer = Column(Text, nullable=True)  # For single correct answers
    correct_answers = Column(JSON, nullable=True)  # For multiple correct answers
    explanation = Column(Text, nullable=True)  # Explanation of the correct answer
    
    # Difficulty and scoring
    difficulty_level = Column(Enum(DifficultyLevel), nullable=False)
    points = Column(Integer, default=1)
    time_limit_seconds = Column(Integer, nullable=True)
    
    # Adaptive learning parameters
    success_threshold = Column(Float, default=0.8)  # Required accuracy to pass
    adaptive_difficulty = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    subtask = relationship("Subtask", back_populates="exercises")
    student_attempts = relationship("StudentExerciseAttempt", back_populates="exercise")

class StudentSubtaskProgress(Base):
    """Tracks student progress through individual subtasks"""
    __tablename__ = 'student_subtask_progress'
    
    student_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id'), primary_key=True)
    subtask_id = Column(UUID(as_uuid=True), ForeignKey('subtasks.id'), primary_key=True)
    
    # Progress tracking
    status = Column(Enum(ProgressStatus), default=ProgressStatus.NOT_STARTED)
    progress_percentage = Column(Float, default=0.0)  # 0-100
    time_spent_minutes = Column(Integer, default=0)
    
    # Performance metrics
    attempts_count = Column(Integer, default=0)
    successful_attempts = Column(Integer, default=0)
    best_score = Column(Float, default=0.0)
    average_score = Column(Float, default=0.0)
    
    # Adaptive learning data
    current_difficulty = Column(Enum(DifficultyLevel), default=DifficultyLevel.INTERMEDIATE)
    mastery_level = Column(Float, default=0.0)  # 0-1 scale
    
    # Timestamps
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    profile = relationship("Profile")
    subtask = relationship("Subtask", back_populates="student_progress")

class StudentExerciseAttempt(Base):
    """Records individual attempts at exercises"""
    __tablename__ = 'student_exercise_attempts'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id'), nullable=False)
    exercise_id = Column(UUID(as_uuid=True), ForeignKey('exercises.id'), nullable=False)
    lesson_id = Column(UUID(as_uuid=True), ForeignKey('Lessons.session_id'), nullable=True)
    
    # Attempt details
    answer = Column(Text, nullable=True)  # Student's answer
    answers = Column(JSON, nullable=True)  # For multiple answers
    is_correct = Column(Boolean, nullable=False)
    score = Column(Float, nullable=False)  # 0-1 scale
    
    # Performance metrics
    response_time_seconds = Column(Float, nullable=True)
    hints_used = Column(Integer, default=0)
    attempts_before_success = Column(Integer, default=1)
    
    # Feedback and learning
    feedback_received = Column(Text, nullable=True)
    student_confidence = Column(Float, nullable=True)  # 0-1 scale
    difficulty_perceived = Column(Enum(DifficultyLevel), nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    profile = relationship("Profile")
    exercise = relationship("Exercise", back_populates="student_attempts")
    lesson = relationship("Lesson")

class AdaptiveLessonPlan(Base):
    """Stores AI-generated personalized lesson plans"""
    __tablename__ = 'adaptive_lesson_plans'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id'), nullable=False)
    topic_id = Column(String, ForeignKey('topics.id'), nullable=False)
    lesson_id = Column(UUID(as_uuid=True), ForeignKey('Lessons.session_id'), nullable=True)
    
    # Lesson plan details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    learning_objectives = Column(JSON, nullable=True)
    estimated_duration_minutes = Column(Integer, nullable=True)
    
    # AI-generated content
    subtask_sequence = Column(JSON, nullable=False)  # Ordered list of subtask IDs
    difficulty_progression = Column(JSON, nullable=True)  # Difficulty changes throughout lesson
    adaptive_parameters = Column(JSON, nullable=True)  # AI parameters for personalization
    
    # Progress tracking
    current_subtask_index = Column(Integer, default=0)
    is_completed = Column(Boolean, default=False)
    completion_percentage = Column(Float, default=0.0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # When the plan becomes stale
    
    # Relationships
    profile = relationship("Profile")
    topic = relationship("Topic")
    lesson = relationship("Lesson")

class LearningAnalytics(Base):
    """Stores detailed learning analytics for insights and improvement"""
    __tablename__ = 'learning_analytics'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey('profiles.id'), nullable=False)
    topic_id = Column(String, ForeignKey('topics.id'), nullable=True)
    subtask_id = Column(UUID(as_uuid=True), ForeignKey('subtasks.id'), nullable=True)
    
    # Learning session data
    session_start = Column(DateTime, nullable=False)
    session_end = Column(DateTime, nullable=True)
    session_duration_minutes = Column(Integer, nullable=True)
    
    # Performance metrics
    exercises_attempted = Column(Integer, default=0)
    exercises_completed = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    accuracy_rate = Column(Float, nullable=True)
    
    # Learning behavior
    time_per_exercise = Column(Float, nullable=True)  # Average time in seconds
    hints_used_total = Column(Integer, default=0)
    skipped_exercises = Column(Integer, default=0)
    
    # Engagement metrics
    engagement_score = Column(Float, nullable=True)  # 0-1 scale
    focus_time_minutes = Column(Integer, default=0)
    breaks_taken = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    profile = relationship("Profile")
    topic = relationship("Topic")
    subtask = relationship("Subtask")

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

# Adaptive learning indexes
Index('ix_student_topic_state_student_id', StudentTopicState.student_id)
Index('ix_student_topic_state_topic_id', StudentTopicState.topic_id)
Index('ix_diagnostic_events_student_id', DiagnosticEvent.student_id)
Index('ix_diagnostic_events_topic_id', DiagnosticEvent.topic_id)
Index('ix_diagnostic_events_created_at', DiagnosticEvent.created_at)

# Create indexes for new models
Index('ix_subtasks_topic_id', Subtask.topic_id)
Index('ix_subtasks_subtask_order', Subtask.subtask_order)
Index('ix_subtasks_subtask_type', Subtask.subtask_type)
Index('ix_exercises_subtask_id', Exercise.subtask_id)
Index('ix_exercises_exercise_type', Exercise.exercise_type)
Index('ix_exercises_difficulty_level', Exercise.difficulty_level)
Index('ix_student_subtask_progress_student_id', StudentSubtaskProgress.student_id)
Index('ix_student_subtask_progress_subtask_id', StudentSubtaskProgress.subtask_id)
Index('ix_student_subtask_progress_status', StudentSubtaskProgress.status)
Index('ix_student_exercise_attempts_student_id', StudentExerciseAttempt.student_id)
Index('ix_student_exercise_attempts_exercise_id', StudentExerciseAttempt.exercise_id)
Index('ix_student_exercise_attempts_lesson_id', StudentExerciseAttempt.lesson_id)
Index('ix_adaptive_lesson_plans_student_id', AdaptiveLessonPlan.student_id)
Index('ix_adaptive_lesson_plans_topic_id', AdaptiveLessonPlan.topic_id)
Index('ix_adaptive_lesson_plans_lesson_id', AdaptiveLessonPlan.lesson_id)
Index('ix_learning_analytics_student_id', LearningAnalytics.student_id)
Index('ix_learning_analytics_topic_id', LearningAnalytics.topic_id)
Index('ix_learning_analytics_session_start', LearningAnalytics.session_start)
