from sqlalchemy import Column, Integer, String, Text, DateTime, Date, ForeignKey, Index, BigInteger, JSON, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

Base = declarative_base()

class OnboardingData(Base):
    __tablename__ = 'onboarding_data'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True))  # References auth.users.id from Supabase Auth
    heard_from = Column(String)
    learning_reason = Column(String)
    daily_goal = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserStatistics(Base):
    __tablename__ = 'user_statistics'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True))  # References auth.users.id from Supabase Auth
    total_lessons = Column(Integer, default=0)
    total_study_time_minutes = Column(Integer, default=0)
    total_tests_completed = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserStreaks(Base):
    __tablename__ = 'user_streaks'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True))  # References auth.users.id from Supabase Auth
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    last_study_date = Column(Date)
    points = Column(Integer, default=0)
    hearts = Column(Integer, default=5)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Prompt(Base):
    __tablename__ = 'prompts'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)  # e.g., 'planning', 'true_false_exercise', 'multiple_choice_exercise'
    description = Column(Text)  # Description of what this prompt is used for
    system_prompt = Column(Text, nullable=False)  # The system prompt for the AI
    user_prompt = Column(Text, nullable=False)  # The user prompt template
    is_active = Column(Boolean, default=True)  # Whether this prompt is currently active
    version = Column(String, default='1.0')  # Version of the prompt
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Optional fields for future use
    category = Column(String)  # e.g., 'exercise_generation', 'lesson_planning', 'content_creation'
    subject = Column(String)  # e.g., 'physics', 'math', 'general'
    difficulty_level = Column(String)  # e.g., 'beginner', 'intermediate', 'advanced'
    language = Column(String, default='et')  # Language code (et for Estonian)
    prompt_metadata = Column(JSON)  # Additional metadata as JSON

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
    subject_guide = Column(JSON)  # JSONB field for subject-specific guidance
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    subject = relationship("Subject", back_populates="topics")

class Lesson(Base):
    __tablename__ = 'Lessons'
    
    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True))  # References auth.users.id from Supabase Auth
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
    plan_status = Column(String, default='creating')  # 'creating', 'ready', 'confirmed', 'in_progress', 'error'
    
    # Relationships
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
    
    user_id = Column(UUID(as_uuid=True), primary_key=True)  # References auth.users.id from Supabase Auth
    topic_id = Column(String, ForeignKey('topics.id'), primary_key=True)
    progress = Column(Integer, nullable=False)  # 0-100
    last_accessed = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    topic = relationship("Topic")

class UserTopicCompletion(Base):
    """Tracks which topics each user has completed"""
    __tablename__ = 'user_topic_completion'
    
    user_id = Column(UUID(as_uuid=True), primary_key=True)  # References auth.users.id from Supabase Auth
    topic_id = Column(String, ForeignKey('topics.id'), primary_key=True)
    
    # Completion tracking
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)
    progress_percentage = Column(Integer, default=0)  # 0-100
    
    # Learning metrics
    mastery_level = Column(Float, default=0.0)  # 0.0-1.0
    last_accessed = Column(DateTime, default=datetime.utcnow)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    topic = relationship("Topic")

class StudentTopicState(Base):
    """Tracks adaptive learning metrics for each student-topic combination"""
    __tablename__ = 'student_topic_state'
    
    student_id = Column(UUID(as_uuid=True), primary_key=True)  # References auth.users.id from Supabase Auth
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
    topic = relationship("Topic")

class DiagnosticEvent(Base):
    """Stores diagnostic and learning interaction events"""
    __tablename__ = 'diagnostic_events'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), nullable=False)  # References auth.users.id from Supabase Auth
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
    subject = relationship("Subject")
    topic = relationship("Topic")

class Tool(Base):
    """Stores available tools and their configurations"""
    __tablename__ = 'tools'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=False)
    tool_type = Column(String, nullable=False)  # exercise, assessment, content, interaction, utility
    version = Column(String, default="1.0.0")
    
    # Tool capabilities
    supported_subjects = Column(JSON, default=[])  # List of supported subjects
    supported_difficulties = Column(JSON, default=[])  # List of supported difficulty levels
    
    # Configuration
    parameters = Column(JSON)  # Tool parameters schema
    max_execution_time = Column(Float, default=30.0)
    
    # Tool status and metadata
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=True)  # Whether tool is available to all users
    created_by = Column(UUID(as_uuid=True))  # References auth.users.id from Supabase Auth
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Additional metadata
    tags = Column(JSON, default=[])  # List of tags for categorization
    usage_count = Column(Integer, default=0)  # Number of times tool has been used
    last_used = Column(DateTime)
    documentation_url = Column(String)  # URL to tool documentation
    source_code_url = Column(String)  # URL to source code if open source

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

# New completion tracking indexes
Index('ix_user_topic_completion_user_id', UserTopicCompletion.user_id)
Index('ix_user_topic_completion_topic_id', UserTopicCompletion.topic_id)

# Adaptive learning indexes
Index('ix_student_topic_state_student_id', StudentTopicState.student_id)
Index('ix_student_topic_state_topic_id', StudentTopicState.topic_id)
Index('ix_diagnostic_events_student_id', DiagnosticEvent.student_id)
Index('ix_diagnostic_events_topic_id', DiagnosticEvent.topic_id)
Index('ix_diagnostic_events_created_at', DiagnosticEvent.created_at)

# Tool indexes
Index('ix_tools_name', Tool.name)
Index('ix_tools_tool_type', Tool.tool_type)
Index('ix_tools_is_active', Tool.is_active)
Index('ix_tools_created_by', Tool.created_by)
