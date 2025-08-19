# Adaptive Lesson System

This document describes the implementation of the adaptive lesson system for Tegus, which provides personalized learning experiences for students based on their proficiency level and focus areas.

## Overview

The adaptive lesson system consists of several key components:

1. **Lesson Plan Creation** - AI-powered lesson planning using the Manus agent
2. **Plan Confirmation** - User confirmation before starting the lesson
3. **Lesson Execution** - Step-by-step lesson progression with adaptive tools
4. **Progress Tracking** - Real-time monitoring of lesson completion

## System Flow

```
User Request → Create Lesson Plan → Manus Process → Plan Ready → User Confirms → Lesson Starts
     ↓              ↓                ↓            ↓           ↓              ↓
Session Created → Background Task → AI Planning → Status: Ready → KINNITA Button → Execute Steps
```

## API Endpoints

### 1. Create Lesson Plan
**POST** `/lessons/create-plan`

Creates a new lesson plan using the Manus agent.

**Request Body:**
```json
{
  "user_id": "string",
  "topic_id": "string", 
  "subject": "string",
  "focus_area": "string (optional)",
  "proficiency_level": "string (optional)",
  "custom_prompt": "string (optional)"
}
```

**Response:**
```json
{
  "session_id": "string",
  "status": "creating",
  "message": "string",
  "plan_ready": false
}
```

### 2. Get Plan Status
**GET** `/lessons/plan-status/{session_id}`

Retrieves the current status of a lesson plan.

**Response:**
```json
{
  "session_id": "string",
  "plan_status": "creating|ready|confirmed|in_progress|error",
  "steps": ["string"],
  "step_statuses": ["string"],
  "step_responses": ["object"],
  "plan_ready": boolean
}
```

### 3. Confirm Lesson Plan
**POST** `/lessons/confirm-plan`

Confirms the lesson plan and starts the lesson execution.

**Request Body:**
```json
{
  "session_id": "string",
  "user_id": "string"
}
```

**Response:**
```json
{
  "session_id": "string",
  "status": "confirmed",
  "message": "string",
  "plan_ready": true
}
```

## Database Schema

### Lessons Table
The `Lessons` table has been extended with a new `plan_status` field:

```sql
ALTER TABLE "Lessons" ADD COLUMN plan_status VARCHAR DEFAULT 'creating';
```

**Plan Status Values:**
- `creating` - Lesson plan is being generated
- `ready` - Lesson plan is ready for user confirmation
- `confirmed` - User has confirmed the plan
- `in_progress` - Lesson is currently being executed
- `error` - An error occurred during plan creation or execution

## Frontend Components

### LessonPlanConfirmation Component

A React Native component that provides the user interface for:
- Viewing lesson plan status
- Displaying lesson steps
- Confirming the lesson plan with the "KINNITA TUNNI PLAAN" button
- Tracking lesson progress

**Key Features:**
- Real-time status updates
- Step-by-step lesson display
- Progress visualization
- Error handling and retry functionality

## Implementation Details

### Background Tasks

The system uses asynchronous background tasks to:
1. **Create Lesson Plans**: Runs the Manus agent to generate personalized lesson content
2. **Execute Lessons**: Processes lesson steps sequentially using the planning flow

### Manus Agent Integration

The Manus agent is integrated through the PlanningFlow to:
- Generate lesson plans based on user requirements
- Execute lesson steps using available tools
- Adapt content based on user progress and responses

### Available Tools

The system leverages existing tools from `app/tool/`:
- **RagSearch** - Content retrieval and research
- **MultipleChoiceExercise** - Interactive quizzes
- **TrueFalseExercise** - True/false questions
- **CalculationExercise** - Mathematical problems
- **CheckSolution** - Answer verification

## Usage Example

### 1. Create a Lesson Plan
```typescript
const response = await fetch('/api/lessons/create-plan', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_id: 'user-123',
    topic_id: 'physics-mechanics',
    subject: 'physics',
    focus_area: 'Force and Motion',
    proficiency_level: 'Beginner'
  })
});

const { session_id } = await response.json();
```

### 2. Monitor Plan Status
```typescript
const statusResponse = await fetch(`/api/lessons/plan-status/${session_id}`);
const { plan_status, plan_ready } = await statusResponse.json();

if (plan_ready) {
  // Show confirmation button
}
```

### 3. Confirm and Start Lesson
```typescript
const confirmResponse = await fetch('/api/lessons/confirm-plan', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id,
    user_id: 'user-123'
  })
});
```

## Testing

Run the comprehensive test suite:

```bash
cd tests
python3 test_adaptive_lesson_system.py
```

The test script covers:
- Lesson plan creation
- Status monitoring
- Plan confirmation
- Lesson execution
- Error handling

## Error Handling

The system includes comprehensive error handling for:
- Network failures
- Database errors
- Agent execution failures
- Invalid user requests
- Timeout scenarios

## Future Enhancements

Potential improvements include:
1. **Real-time Collaboration** - Multi-user lesson sessions
2. **Advanced Analytics** - Learning pattern analysis
3. **Content Personalization** - Dynamic content adaptation
4. **Integration APIs** - Third-party content providers
5. **Offline Support** - Cached lesson content

## Troubleshooting

### Common Issues

1. **Plan Creation Timeout**
   - Check Manus agent configuration
   - Verify database connectivity
   - Review agent tool availability

2. **Lesson Execution Failures**
   - Check step dependencies
   - Verify tool configurations
   - Review error logs

3. **Status Update Delays**
   - Check background task execution
   - Verify polling intervals
   - Review database performance

### Debug Mode

Enable debug logging by setting:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Security Considerations

- User authentication required for all endpoints
- Session ownership validation
- Input sanitization and validation
- Rate limiting for API endpoints
- Secure database connections

## Performance Optimization

- Asynchronous background processing
- Database connection pooling
- Caching for frequently accessed data
- Efficient query optimization
- Background task queuing

## Monitoring and Logging

The system provides comprehensive logging for:
- API requests and responses
- Background task execution
- Error conditions and stack traces
- Performance metrics
- User interaction patterns

## Support

For technical support or questions about the adaptive lesson system, please refer to:
- System logs in `logs/` directory
- Database query performance
- Agent execution status
- API endpoint health checks
