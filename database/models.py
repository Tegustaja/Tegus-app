from sqlalchemy import Column, Integer, String, Text, DateTime, Date, ForeignKey, Index, BigInteger, JSON, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

Base = declarative_base()

class Profile(Base):
    __tablename__ = 'profiles'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String)
    avatar_url = Column(String)
    is_admin = Column(Boolean, default=False)
    admin_expires_at = Column(DateTime)  # When admin privileges expire
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
    plan_status = Column(String, default='creating')  # 'creating', 'ready', 'confirmed', 'in_progress', 'error'
    
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
