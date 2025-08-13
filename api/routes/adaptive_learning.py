from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import logging

from app.logger import logger
from app.backtofront.connect_db import get_data

router = APIRouter()

# Pydantic models
class ProbeItem(BaseModel):
    id: str
    difficulty: str  # 'easy', 'medium', 'hard'
    prompt: str
    expected_type: str  # 'mcq', 'numeric', 'free'
    options: Optional[List[str]] = None  # For MCQ questions

class DiagnosticStartRequest(BaseModel):
    student_id: str
    subject: str
    topic_id: str

class DiagnosticStartResponse(BaseModel):
    items: List[ProbeItem]

class EventSubmission(BaseModel):
    student_id: str
    subject: str
    topic_id: str
    event_type: str  # 'probe', 'exercise', 'explain'
    correct: bool
    latency_ms: int
    confidence: Optional[float] = None
    item_id: Optional[str] = None
    difficulty: Optional[str] = None
    result_metadata: Optional[Dict[str, Any]] = None

class EventResponse(BaseModel):
    ok: bool
    updated_metrics: Dict[str, Any]

class LessonStartRequest(BaseModel):
    student_id: str
    subject: str
    topic_id: str

class LessonTurn(BaseModel):
    mode: str  # 'explain' or 'exercise'
    content: str
    metadata: Optional[Dict[str, Any]] = None
    next_probe: Optional[ProbeItem] = None

class LessonNextRequest(BaseModel):
    student_id: str
    subject: str
    topic_id: str
    last_turn_result: EventSubmission

class TopicMetrics(BaseModel):
    mastery: float  # 0-1
    stability: float  # 0-1
    pace: float  # 0-1
    calibration: float  # 0-1
    learning_index: int  # 0-100
    difficulty_band: str

# Sample diagnostic items (in production, these would come from a database)
SAMPLE_PROBES = {
    "physics": {
        "mechanics": [
            {
                "id": "p_m_1",
                "difficulty": "easy",
                "prompt": "What is the SI unit for force?",
                "expected_type": "mcq",
                "options": ["Newton", "Joule", "Watt", "Pascal"]
            },
            {
                "id": "p_m_2", 
                "difficulty": "medium",
                "prompt": "A car accelerates from 0 to 20 m/s in 5 seconds. What is its acceleration?",
                "expected_type": "numeric"
            },
            {
                "id": "p_m_3",
                "difficulty": "hard",
                "prompt": "Explain the relationship between work and energy in a closed system.",
                "expected_type": "free"
            }
        ]
    }
}

# Adaptive learning algorithms
def clamp_01(x: float) -> float:
    """Clamp value between 0 and 1"""
    return max(0.0, min(1.0, x))

def ema(prev: float, value: float, alpha: float) -> float:
    """Exponential moving average"""
    return prev + alpha * (value - prev)

def update_mastery(prev: float, correct: bool, latency_ms: int, confidence: Optional[float] = None) -> float:
    """Update mastery based on correctness, speed, and confidence"""
    speed_factor = 1.0 if latency_ms < 15000 else 0.6
    conf_factor = 0.7 + 0.3 * (confidence or 0.5) if confidence is not None else 1.0
    target = 1.0 if correct else 0.0
    alpha = 0.15 * speed_factor * conf_factor
    return clamp_01(prev + alpha * (target - prev))

def update_stability(prev_correct_ema: float, prev_volatility: float, correct: bool) -> tuple[float, float, float]:
    """Update stability via volatility of correctness around its EMA"""
    c = 1.0 if correct else 0.0
    correct_ema = ema(prev_correct_ema, c, 0.2)
    volatility = ema(prev_volatility, abs(c - correct_ema), 0.1)
    stability = 1.0 - volatility
    return correct_ema, volatility, clamp_01(stability)

def update_pace(prev_pace: float, latency_ms: int, target_ms: int = 20000) -> float:
    """Update pace: 1 means very fast at/under target, 0 means much slower"""
    ratio = latency_ms / target_ms
    pace_score = clamp_01(1.0 - max(0.0, ratio - 1.0))
    return ema(prev_pace, pace_score, 0.1)

def update_calibration(prev_calibration: float, correct: bool, confidence: Optional[float]) -> float:
    """Update calibration: 1 - absolute error between confidence and correctness"""
    if confidence is None:
        return prev_calibration
    c = 1.0 if correct else 0.0
    score = 1.0 - abs(confidence - c)
    return ema(prev_calibration, score, 0.1)

def compute_learning_index(mastery: float, stability: float, pace: float, calibration: float) -> int:
    """Compute overall learning index (0-100)"""
    li = 0.55 * mastery + 0.15 * stability + 0.15 * pace + 0.15 * calibration
    return round(li * 100)

def difficulty_band(mastery: float) -> str:
    """Determine difficulty band based on mastery"""
    if mastery < 0.35:
        return "intro"
    elif mastery < 0.75:
        return "core"
    else:
        return "stretch"

def decide_next_mode(recent_events: List[Dict[str, Any]]) -> str:
    """Decide whether to explain or exercise next"""
    if len(recent_events) < 2:
        return "explain"
    
    recent = recent_events[-3:]  # Last 3 events
    corrects = sum(1 for e in recent if e.get('correct', False))
    misses = sum(1 for e in recent if not e.get('correct', True))
    avg_latency = sum(e.get('latency_ms', 0) for e in recent) / len(recent)
    
    if misses >= 2:
        return "explain"
    if corrects >= 1 and avg_latency < 20000:
        return "exercise"
    return "explain"

@router.post("/diagnostics/start", response_model=DiagnosticStartResponse)
async def start_diagnostic(request: DiagnosticStartRequest):
    """Start a diagnostic session for a student-topic combination"""
    try:
        # Get sample probes for the topic (in production, query database)
        topic_probes = SAMPLE_PROBES.get(request.subject, {}).get(request.topic_id, [])
        
        if not topic_probes:
            # Fallback to generic probes
            topic_probes = [
                {
                    "id": f"generic_{uuid.uuid4().hex[:8]}",
                    "difficulty": "medium",
                    "prompt": "Please answer this question to help us understand your current level.",
                    "expected_type": "free"
                }
            ]
        
        return DiagnosticStartResponse(items=topic_probes)
    
    except Exception as e:
        logger.error(f"Error starting diagnostic: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start diagnostic")

@router.post("/events", response_model=EventResponse)
async def submit_event(event: EventSubmission):
    """Submit a learning event and update metrics"""
    try:
        # Get current topic state
        db = get_data()
        
        # Query current state
        query = """
        SELECT * FROM student_topic_state 
        WHERE student_id = %s AND topic_id = %s
        """
        result = db.execute(query, (event.student_id, event.topic_id))
        current_state = result.fetchone()
        
        if not current_state:
            # Initialize new state
            current_state = {
                'mastery': 0.0,
                'correct_ema': 0.0,
                'volatility': 0.5,
                'pace': 0.5,
                'calibration': 0.5
            }
        
        # Update metrics
        mastery = update_mastery(
            current_state.get('mastery', 0.0),
            event.correct,
            event.latency_ms,
            event.confidence
        )
        
        correct_ema, volatility, stability = update_stability(
            current_state.get('correct_ema', 0.0),
            current_state.get('volatility', 0.5),
            event.correct
        )
        
        pace = update_pace(
            current_state.get('pace', 0.5),
            event.latency_ms
        )
        
        calibration = update_calibration(
            current_state.get('calibration', 0.5),
            event.correct,
            event.confidence
        )
        
        learning_index = compute_learning_index(mastery, stability, pace, calibration)
        difficulty_band_val = difficulty_band(mastery)
        
        # Save updated state
        if current_state.get('student_id'):
            # Update existing
            update_query = """
            UPDATE student_topic_state SET
                mastery = %s, correct_ema = %s, volatility = %s, pace = %s, 
                calibration = %s, learning_index = %s, difficulty_band = %s,
                last_seen_at = NOW(), updated_at = NOW()
            WHERE student_id = %s AND topic_id = %s
            """
            db.execute(update_query, (
                mastery, correct_ema, volatility, pace, calibration,
                learning_index, difficulty_band_val, event.student_id, event.topic_id
            ))
        else:
            # Insert new
            insert_query = """
            INSERT INTO student_topic_state (
                student_id, topic_id, mastery, correct_ema, volatility, pace,
                calibration, learning_index, difficulty_band, last_seen_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            """
            db.execute(insert_query, (
                event.student_id, event.topic_id, mastery, correct_ema, volatility,
                pace, calibration, learning_index, difficulty_band_val
            ))
        
        # Save event
        event_query = """
        INSERT INTO diagnostic_events (
            id, student_id, subject_id, topic_id, event_type, correct, latency_ms,
            confidence, item_id, difficulty, result_metadata, created_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """
        db.execute(event_query, (
            str(uuid.uuid4()), event.student_id, event.subject, event.topic_id,
            event.event_type, event.correct, event.latency_ms, event.confidence,
            event.item_id, event.difficulty, event.result_metadata
        ))
        
        db.commit()
        
        return EventResponse(
            ok=True,
            updated_metrics={
                "mastery": round(mastery * 100, 1),
                "stability": round(stability * 100, 1),
                "pace": round(pace * 100, 1),
                "calibration": round(calibration * 100, 1),
                "learning_index": learning_index,
                "difficulty_band": difficulty_band_val
            }
        )
    
    except Exception as e:
        logger.error(f"Error submitting event: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to submit event")

@router.post("/lesson/start", response_model=LessonTurn)
async def start_lesson(request: LessonStartRequest):
    """Start a lesson session"""
    try:
        # For now, start with an explanation
        # In production, this would check if diagnostic is needed first
        return LessonTurn(
            mode="explain",
            content="Welcome! Let's start learning this topic. I'll explain the key concepts and then we'll practice together.",
            metadata={"difficulty_band": "intro"}
        )
    
    except Exception as e:
        logger.error(f"Error starting lesson: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start lesson")

@router.post("/lesson/next", response_model=LessonTurn)
async def next_lesson_turn(request: LessonNextRequest):
    """Get the next lesson turn based on previous results"""
    try:
        # Get recent events to decide mode
        db = get_data()
        query = """
        SELECT event_type, correct, latency_ms, confidence 
        FROM diagnostic_events 
        WHERE student_id = %s AND topic_id = %s 
        ORDER BY created_at DESC LIMIT 5
        """
        result = db.execute(query, (request.student_id, request.topic_id))
        recent_events = result.fetchall()
        
        # Convert to dict format for decision logic
        recent_dicts = [
            {
                'event_type': row[0],
                'correct': row[1],
                'latency_ms': row[2],
                'confidence': row[3]
            }
            for row in recent_events
        ]
        
        mode = decide_next_mode(recent_dicts)
        
        if mode == "explain":
            content = "Let me explain this concept in more detail. Here's what you need to know..."
        else:
            content = "Now let's practice! Here's an exercise to test your understanding..."
        
        return LessonTurn(
            mode=mode,
            content=content,
            metadata={"difficulty_band": "intro"}  # In production, get from current state
        )
    
    except Exception as e:
        logger.error(f"Error getting next lesson turn: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get next lesson turn")

@router.get("/metrics/topic")
async def get_topic_metrics(student_id: str, topic_id: str):
    """Get current metrics for a student-topic combination"""
    try:
        db = get_data()
        query = """
        SELECT mastery, correct_ema, volatility, pace, calibration, 
               learning_index, difficulty_band
        FROM student_topic_state 
        WHERE student_id = %s AND topic_id = %s
        """
        result = db.execute(query, (student_id, topic_id))
        state = result.fetchone()
        
        if not state:
            return {
                "mastery": 0,
                "stability": 50,
                "pace": 50,
                "calibration": 50,
                "learning_index": 0,
                "difficulty_band": "intro"
            }
        
        # Calculate stability from volatility
        stability = max(0, 100 - (state[2] * 100))  # volatility is 0-1
        
        return {
            "mastery": round(state[0] * 100, 1),
            "stability": round(stability, 1),
            "pace": round(state[3] * 100, 1),
            "calibration": round(state[4] * 100, 1),
            "learning_index": state[5],
            "difficulty_band": state[6]
        }
    
    except Exception as e:
        logger.error(f"Error getting topic metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get topic metrics")

