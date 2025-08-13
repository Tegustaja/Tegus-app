# Adaptive Learning System

## Overview

The Adaptive Learning System is a comprehensive solution that dynamically adapts educational content based on student performance. It uses machine learning algorithms to track student mastery, stability, pace, and calibration, then automatically adjusts between explanation and exercise modes.

## Architecture

### Backend Components

#### 1. Database Models (`database/models.py`)
- **`StudentTopicState`**: Tracks learning metrics per student-topic combination
- **`DiagnosticEvent`**: Stores all learning interactions and their outcomes

#### 2. API Endpoints (`api/routes/adaptive_learning.py`)
- **`POST /diagnostics/start`**: Begin diagnostic assessment
- **`POST /events`**: Submit learning events and update metrics
- **`POST /lesson/start`**: Start a lesson session
- **`POST /lesson/next`**: Get next lesson turn based on performance
- **`GET /metrics/topic`**: Retrieve current learning metrics

#### 3. Core Algorithms
- **Mastery Update**: Exponential moving average with speed and confidence factors
- **Stability Calculation**: Volatility-based consistency measurement
- **Pace Assessment**: Response time relative to target benchmarks
- **Calibration**: Alignment between self-reported confidence and actual performance
- **Learning Index**: Weighted combination of all metrics (0-100 scale)

### Frontend Components

#### 1. Services (`tegus-frontend/services/adaptive-learning-service.ts`)
- API client functions for all adaptive learning operations
- Helper functions for timer creation and event submission

#### 2. UI Components
- **`LearningMetricCard`**: Individual metric display with progress bars
- **`LearningMetricsGrid`**: Complete metrics dashboard
- **`DiagnosticProbe`**: Individual diagnostic question interface
- **`DiagnosticSession`**: Multi-question diagnostic flow
- **`AdaptiveLessonFlow`**: Main lesson orchestrator

## How It Works

### 1. Initial Assessment
When a student starts learning a new topic:
1. System checks for existing metrics
2. If none exist, starts diagnostic assessment (3-5 questions)
3. Questions cover easy, medium, and hard difficulty levels
4. Student provides answers with confidence ratings

### 2. Metric Calculation
After each interaction:
1. **Mastery**: Updated based on correctness, speed, and confidence
2. **Stability**: Measures consistency of performance over time
3. **Pace**: Evaluates response speed relative to expectations
4. **Calibration**: Assesses self-awareness accuracy
5. **Learning Index**: Computed as weighted average (55% mastery, 15% each for others)

### 3. Adaptive Content Selection
The system automatically decides between:
- **Explain Mode**: When student shows confusion or needs scaffolding
- **Exercise Mode**: When student demonstrates understanding and readiness

### 4. Continuous Adaptation
- Metrics update after every interaction
- Difficulty bands adjust automatically (intro → core → stretch)
- Content complexity scales with student progress

## Data Flow

```
Student Interaction → Event Submission → Metric Update → Mode Decision → Content Generation
       ↓                    ↓              ↓              ↓              ↓
   Answer + Time    POST /events    Algorithm    decide_next_mode   Lesson Turn
   + Confidence     + Metadata      Update       + Recent Events    + Metadata
```

## Usage Examples

### Starting a Diagnostic
```typescript
import { startDiagnostic } from '@/services/adaptive-learning-service';

const probes = await startDiagnostic(studentId, 'physics', 'mechanics');
// Returns array of ProbeItem objects
```

### Submitting an Event
```typescript
import { submitEvent, createEventSubmission } from '@/services/adaptive-learning-service';

const event = createEventSubmission(
  studentId,
  'physics',
  'mechanics',
  'probe',
  true, // correct
  8000, // 8 seconds
  0.9   // 90% confidence
);

const updatedMetrics = await submitEvent(event);
// Returns updated TopicMetrics
```

### Getting Lesson Content
```typescript
import { startLesson, nextLessonTurn } from '@/services/adaptive-learning-service';

// Start lesson
const lessonTurn = await startLesson(studentId, 'physics', 'mechanics');

// Get next turn after interaction
const nextTurn = await nextLessonTurn(studentId, 'physics', 'mechanics', eventSubmission);
```

## Configuration

### Environment Variables
```bash
EXPO_PUBLIC_API_URL=http://localhost:8000  # Backend API URL
```

### Database Migration
```bash
# Run the migration to create new tables
alembic upgrade head
```

## Customization

### Adding New Diagnostic Questions
Edit the `SAMPLE_PROBES` dictionary in `api/routes/adaptive_learning.py`:

```python
SAMPLE_PROBES = {
    "physics": {
        "mechanics": [
            {
                "id": "p_m_4",
                "difficulty": "medium",
                "prompt": "Your custom question here?",
                "expected_type": "mcq",
                "options": ["Option A", "Option B", "Option C", "Option D"]
            }
        ]
    }
}
```

### Adjusting Algorithm Parameters
Modify the constants in the update functions:

```python
def update_mastery(prev, correct, latency_ms, confidence=None):
    speed_factor = 1.0 if latency_ms < 15000 else 0.6  # Adjust 15000ms threshold
    alpha_base = 0.15  # Adjust learning rate
    # ... rest of function
```

### Customizing Metric Weights
Change the learning index calculation:

```python
def compute_learning_index(mastery, stability, pace, calibration):
    # Adjust weights as needed
    li = 0.55 * mastery + 0.15 * stability + 0.15 * pace + 0.15 * calibration
    return round(li * 100)
```

## Testing

### Backend Testing
```bash
# Run the test script
python test_adaptive_learning.py
```

### Frontend Testing
```typescript
// Test individual components
import { LearningMetricsGrid } from '@/components/learning-metric-card';

const testMetrics = {
  mastery: 75,
  stability: 80,
  pace: 70,
  calibration: 85,
  learning_index: 76,
  difficulty_band: 'core'
};

<LearningMetricsGrid metrics={testMetrics} />
```

## Performance Considerations

### Database Optimization
- Indexes on frequently queried columns
- Efficient queries using composite keys
- Minimal data updates per interaction

### Algorithm Efficiency
- O(1) metric updates using exponential moving averages
- Minimal state storage per student-topic combination
- Batch processing for multiple events

### Frontend Performance
- Lazy loading of diagnostic questions
- Efficient state management with React hooks
- Minimal re-renders through proper component structure

## Future Enhancements

### Phase 2: Advanced Adaptation
- [ ] Subject-level onboarding assessments
- [ ] Cross-topic skill transfer detection
- [ ] Personalized learning paths
- [ ] Spaced repetition scheduling

### Phase 3: Content Generation
- [ ] Dynamic question generation
- [ ] Adaptive difficulty progression
- [ ] Personalized explanations
- [ ] Multi-modal content support

### Phase 4: Analytics & Insights
- [ ] Learning pattern analysis
- [ ] Predictive performance modeling
- [ ] Teacher dashboard
- [ ] A/B testing framework

## Troubleshooting

### Common Issues

1. **API Connection Errors**
   - Verify backend is running on correct port
   - Check `EXPO_PUBLIC_API_URL` environment variable
   - Ensure CORS is properly configured

2. **Database Errors**
   - Run `alembic upgrade head` to create tables
   - Check database connection settings
   - Verify foreign key constraints

3. **Metric Calculation Issues**
   - Ensure all required fields are provided in events
   - Check for division by zero in algorithms
   - Verify data types match expected formats

### Debug Mode
Enable detailed logging by setting log level to DEBUG in backend configuration.

## Contributing

When adding new features:
1. Update database models if needed
2. Add corresponding API endpoints
3. Create frontend service functions
4. Build UI components
5. Add comprehensive tests
6. Update documentation

## License

This system is part of the Tegus project and follows the same licensing terms.

