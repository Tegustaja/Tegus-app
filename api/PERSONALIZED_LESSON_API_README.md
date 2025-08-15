# Personalized Lesson Structure FastAPI API Documentation

This document describes the FastAPI endpoints for the personalized lesson structure system in the Tegus education app. The system supports creating unique, personalized lessons for each student with the ability to extend content during learning.

## API Overview

The personalized lesson structure API is organized into five main categories:

1. **Lesson Parts** (`/lesson-parts`) - Manage individual parts within lessons
2. **Personalized Exercises** (`/personalized-exercises`) - Manage exercises within lesson parts
3. **Subtasks** (`/subtasks`) - Manage optional subtasks under exercises
4. **Personalized Progress** (`/personalized-progress`) - Track learning progress at every level
5. **Lesson Extensions** (`/lesson-extensions`) - Handle lesson extensions during learning

## Base URL

All endpoints are relative to your FastAPI server base URL:
```
http://your-server.com/api/
```

## Authentication

All endpoints require proper authentication. Ensure you have valid credentials when making requests.

## 1. Lesson Parts API (`/lesson-parts`)

### Create Lesson Part
- **POST** `/lesson-parts/`
- **Description**: Create a new lesson part within a lesson
- **Request Body**:
  ```json
  {
    "lesson_id": "uuid",
    "title": "string",
    "description": "string (optional)",
    "part_order": "integer > 0"
  }
  ```
- **Response**: `LessonPartResponse`

### Get Lesson Part
- **GET** `/lesson-parts/{lesson_part_id}`
- **Description**: Get a specific lesson part by ID
- **Response**: `LessonPartResponse`

### Get Lesson Part with Exercises
- **GET** `/lesson-parts/{lesson_part_id}/with-exercises`
- **Description**: Get a lesson part with all its exercises
- **Response**: `LessonPartWithExercisesResponse`

### Update Lesson Part
- **PUT** `/lesson-parts/{lesson_part_id}`
- **Description**: Update an existing lesson part
- **Request Body**: `UpdateLessonPartRequest`
- **Response**: `LessonPartResponse`

### Delete Lesson Part
- **DELETE** `/lesson-parts/{lesson_part_id}`
- **Description**: Delete a lesson part (cascades to exercises and subtasks)
- **Response**: Success message

### Get Lesson Parts by Lesson
- **GET** `/lesson-parts/lesson/{lesson_id}`
- **Description**: Get all lesson parts for a specific lesson, ordered by part_order
- **Response**: List of `LessonPartResponse`

### Complete Lesson Part
- **POST** `/lesson-parts/{lesson_part_id}/complete`
- **Description**: Mark a lesson part as completed
- **Response**: Success message

## 2. Personalized Exercises API (`/personalized-exercises`)

### Create Exercise
- **POST** `/personalized-exercises/`
- **Description**: Create a new exercise within a lesson part
- **Request Body**:
  ```json
  {
    "lesson_part_id": "uuid",
    "exercise_type": "multiple_choice|true_false|calculation|explanation|interactive",
    "title": "string",
    "content": "string",
    "instructions": "string (optional)",
    "correct_answer": "string (optional)",
    "explanation": "string (optional)",
    "difficulty_level": "easy|medium|hard",
    "exercise_order": "integer > 0"
  }
  ```
- **Response**: `ExerciseResponse`

### Get Exercise
- **GET** `/personalized-exercises/{exercise_id}`
- **Description**: Get a specific exercise by ID
- **Response**: `ExerciseResponse`

### Get Exercise with Subtasks
- **GET** `/personalized-exercises/{exercise_id}/with-subtasks`
- **Description**: Get an exercise with all its subtasks
- **Response**: `ExerciseWithSubtasksResponse`

### Update Exercise
- **PUT** `/personalized-exercises/{exercise_id}`
- **Description**: Update an existing exercise
- **Request Body**: `UpdateExerciseRequest`
- **Response**: `ExerciseResponse`

### Delete Exercise
- **DELETE** `/personalized-exercises/{exercise_id}`
- **Description**: Delete an exercise (cascades to subtasks)
- **Response**: Success message

### Get Exercises by Lesson Part
- **GET** `/personalized-exercises/lesson-part/{lesson_part_id}`
- **Description**: Get all exercises for a specific lesson part, ordered by exercise_order
- **Response**: List of `ExerciseResponse`

### Get Exercises by Type
- **GET** `/personalized-exercises/type/{exercise_type}`
- **Description**: Get all exercises of a specific type
- **Response**: List of `ExerciseResponse`

### Get Exercises by Difficulty
- **GET** `/personalized-exercises/difficulty/{difficulty_level}`
- **Description**: Get all exercises of a specific difficulty level
- **Response**: List of `ExerciseResponse`

### Complete Exercise
- **POST** `/personalized-exercises/{exercise_id}/complete`
- **Description**: Mark an exercise as completed
- **Response**: Success message

## 3. Subtasks API (`/subtasks`)

### Create Subtask
- **POST** `/subtasks/`
- **Description**: Create a new subtask under an exercise
- **Request Body**:
  ```json
  {
    "exercise_id": "uuid",
    "title": "string",
    "content": "string",
    "subtask_type": "explanation|practice|reinforcement|extension",
    "subtask_order": "integer > 0",
    "is_optional": "boolean (default: true)"
  }
  ```
- **Response**: `SubtaskResponse`

### Get Subtask
- **GET** `/subtasks/{subtask_id}`
- **Description**: Get a specific subtask by ID
- **Response**: `SubtaskResponse`

### Update Subtask
- **PUT** `/subtasks/{subtask_id}`
- **Description**: Update an existing subtask
- **Request Body**: `UpdateSubtaskRequest`
- **Response**: `SubtaskResponse`

### Delete Subtask
- **DELETE** `/subtasks/{subtask_id}`
- **Description**: Delete a subtask
- **Response**: Success message

### Get Subtasks by Exercise
- **GET** `/subtasks/exercise/{exercise_id}`
- **Description**: Get all subtasks for a specific exercise, ordered by subtask_order
- **Response**: List of `SubtaskResponse`

### Get Subtasks by Type
- **GET** `/subtasks/type/{subtask_type}`
- **Description**: Get all subtasks of a specific type
- **Response**: List of `SubtaskResponse`

### Get Subtasks by Optional Status
- **GET** `/subtasks/optional/{is_optional}`
- **Description**: Get all subtasks by their optional status
- **Response**: List of `SubtaskResponse`

### Complete Subtask
- **POST** `/subtasks/{subtask_id}/complete`
- **Description**: Mark a subtask as completed
- **Response**: Success message

### Toggle Subtask Optional Status
- **POST** `/subtasks/{subtask_id}/toggle-optional`
- **Description**: Toggle the optional status of a subtask
- **Response**: Status update message

## 4. Personalized Progress API (`/personalized-progress`)

### Create/Update Lesson Part Progress
- **POST** `/personalized-progress/lesson-part`
- **Description**: Create or update progress for a lesson part
- **Request Body**:
  ```json
  {
    "lesson_part_id": "uuid",
    "user_id": "uuid",
    "status": "not_started|in_progress|completed",
    "progress_percentage": "integer 0-100",
    "time_spent_minutes": "integer >= 0"
  }
  ```
- **Response**: `LessonPartProgressResponse`

### Get Lesson Part Progress
- **GET** `/personalized-progress/lesson-part/{lesson_part_id}/user/{user_id}`
- **Description**: Get progress for a specific lesson part and user
- **Response**: `LessonPartProgressResponse`

### Create/Update Exercise Progress
- **POST** `/personalized-progress/exercise`
- **Description**: Create or update progress for an exercise
- **Request Body**:
  ```json
  {
    "exercise_id": "uuid",
    "user_id": "uuid",
    "status": "not_started|in_progress|completed|failed",
    "attempts": "integer >= 0",
    "correct_attempts": "integer >= 0",
    "time_spent_minutes": "integer >= 0",
    "user_answer": "string (optional)",
    "is_correct": "boolean (optional)"
  }
  ```
- **Response**: `ExerciseProgressResponse`

### Get Exercise Progress
- **GET** `/personalized-progress/exercise/{exercise_id}/user/{user_id}`
- **Description**: Get progress for a specific exercise and user
- **Response**: `ExerciseProgressResponse`

### Create/Update Subtask Progress
- **POST** `/personalized-progress/subtask`
- **Description**: Create or update progress for a subtask
- **Request Body**:
  ```json
  {
    "subtask_id": "uuid",
    "user_id": "uuid",
    "status": "not_started|in_progress|completed",
    "time_spent_minutes": "integer >= 0"
  }
  ```
- **Response**: `SubtaskProgressResponse`

### Get Subtask Progress
- **GET** `/personalized-progress/subtask/{subtask_id}/user/{user_id}`
- **Description**: Get progress for a specific subtask and user
- **Response**: `SubtaskProgressResponse`

### Get User Lesson Progress Summary
- **GET** `/personalized-progress/user/{user_id}/lesson/{lesson_id}/summary`
- **Description**: Get overall progress summary for a user in a specific lesson
- **Response**: `UserProgressSummary`

### Get User Progress Overview
- **GET** `/personalized-progress/user/{user_id}/overview`
- **Description**: Get overview of all user progress across all lessons
- **Response**: Progress overview object

## 5. Lesson Extensions API (`/lesson-extensions`)

### Create Lesson Extension
- **POST** `/lesson-extensions/`
- **Description**: Create a new lesson extension request
- **Request Body**:
  ```json
  {
    "lesson_id": "uuid",
    "user_id": "uuid",
    "extension_type": "lesson_part|exercise|subtask",
    "parent_id": "uuid (optional, required for exercise/subtask extensions)",
    "extension_reason": "string (optional)"
  }
  ```
- **Response**: `LessonExtensionResponse`

### Get Lesson Extension
- **GET** `/lesson-extensions/{extension_id}`
- **Description**: Get a specific lesson extension by ID
- **Response**: `LessonExtensionResponse`

### Get Extensions by Lesson
- **GET** `/lesson-extensions/lesson/{lesson_id}`
- **Description**: Get all extensions for a specific lesson
- **Response**: List of `LessonExtensionResponse`

### Get Extensions by User
- **GET** `/lesson-extensions/user/{user_id}`
- **Description**: Get all extensions created by a specific user
- **Response**: List of `LessonExtensionResponse`

### Get Extensions by Type
- **GET** `/lesson-extensions/type/{extension_type}`
- **Description**: Get all extensions of a specific type
- **Response**: List of `LessonExtensionResponse`

### Get Extension with Content
- **GET** `/lesson-extensions/{extension_id}/with-content`
- **Description**: Get a lesson extension with its associated content
- **Response**: `ExtensionWithContentResponse`

### Delete Lesson Extension
- **DELETE** `/lesson-extensions/{extension_id}`
- **Description**: Delete a lesson extension
- **Response**: Success message

### Get User Extensions for Lesson
- **GET** `/lesson-extensions/lesson/{lesson_id}/user/{user_id}`
- **Description**: Get all extensions created by a specific user for a specific lesson
- **Response**: List of `LessonExtensionResponse`

### Get Extension Type Analytics
- **GET** `/lesson-extensions/analytics/extension-types`
- **Description**: Get analytics on extension types across all lessons
- **Response**: Analytics object

### Get User Extension Analytics
- **GET** `/lesson-extensions/analytics/user/{user_id}`
- **Description**: Get analytics on extensions created by a specific user
- **Response**: User analytics object

## Data Models

### Common Fields
All response models include:
- `id`: Unique identifier (UUID)
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

### Status Values
- **Progress Status**: `not_started`, `in_progress`, `completed`, `failed`
- **Exercise Types**: `multiple_choice`, `true_false`, `calculation`, `explanation`, `interactive`
- **Subtask Types**: `explanation`, `practice`, `reinforcement`, `extension`
- **Difficulty Levels**: `easy`, `medium`, `hard`
- **Extension Types**: `lesson_part`, `exercise`, `subtask`

## Error Handling

All endpoints return appropriate HTTP status codes:
- `200 OK`: Successful operation
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

Error responses include a `detail` field with error information.

## Usage Examples

### Creating a Complete Lesson Structure

```bash
# 1. Create a lesson part
curl -X POST "http://localhost:8000/lesson-parts/" \
  -H "Content-Type: application/json" \
  -d '{
    "lesson_id": "lesson-uuid",
    "title": "Introduction to Forces",
    "description": "Learn the basics of forces",
    "part_order": 1
  }'

# 2. Create an exercise in the lesson part
curl -X POST "http://localhost:8000/personalized-exercises/" \
  -H "Content-Type: application/json" \
  -d '{
    "lesson_part_id": "part-uuid",
    "exercise_type": "multiple_choice",
    "title": "What is force?",
    "content": "Which of the following best describes force?",
    "difficulty_level": "easy",
    "exercise_order": 1
  }'

# 3. Create a subtask for the exercise
curl -X POST "http://localhost:8000/subtasks/" \
  -H "Content-Type: application/json" \
  -d '{
    "exercise_id": "exercise-uuid",
    "title": "Additional Explanation",
    "content": "Force is a push or pull that can change motion",
    "subtask_type": "explanation",
    "subtask_order": 1
  }'

# 4. Track progress
curl -X POST "http://localhost:8000/personalized-progress/exercise" \
  -H "Content-Type: application/json" \
  -d '{
    "exercise_id": "exercise-uuid",
    "user_id": "user-uuid",
    "status": "completed",
    "attempts": 1,
    "correct_attempts": 1,
    "time_spent_minutes": 5,
    "user_answer": "A push or pull",
    "is_correct": true
  }'
```

### Extending a Lesson During Learning

```bash
# Request an extension
curl -X POST "http://localhost:8000/lesson-extensions/" \
  -H "Content-Type: application/json" \
  -d '{
    "lesson_id": "lesson-uuid",
    "user_id": "user-uuid",
    "extension_type": "exercise",
    "parent_id": "part-uuid",
    "extension_reason": "Student needs more practice with force concepts"
  }'

# Create the new exercise
curl -X POST "http://localhost:8000/personalized-exercises/" \
  -H "Content-Type: application/json" \
  -d '{
    "lesson_part_id": "part-uuid",
    "exercise_type": "calculation",
    "title": "Force Calculation Practice",
    "content": "Calculate the net force on an object...",
    "difficulty_level": "medium",
    "exercise_order": 2
  }'
```

## Best Practices

1. **Order Management**: Always use sequential order values (1, 2, 3...) for parts, exercises, and subtasks
2. **Progress Tracking**: Update progress incrementally as students work through content
3. **Extensions**: Use extensions to adapt lessons based on student needs
4. **Validation**: Validate all input data before processing
5. **Error Handling**: Implement proper error handling for all operations
6. **Performance**: Use appropriate database indexes for frequently queried fields

## Rate Limiting

Consider implementing rate limiting for:
- Progress updates (to prevent spam)
- Extension requests (to prevent abuse)
- Bulk operations (to prevent server overload)

## Security Considerations

1. **Authentication**: Ensure all endpoints require valid authentication
2. **Authorization**: Verify users can only access their own data
3. **Input Validation**: Validate all input data to prevent injection attacks
4. **Audit Logging**: Log all operations for security and compliance

## Monitoring and Analytics

The API provides several analytics endpoints:
- Extension type analytics across all lessons
- User-specific extension analytics
- Progress tracking and completion rates
- Time spent on different components

Use these endpoints to monitor system usage and identify areas for improvement.

## Conclusion

This API provides a comprehensive foundation for personalized learning experiences. The modular design allows for flexible lesson structures while maintaining data integrity and providing detailed progress tracking. The extension system enables adaptive learning based on student needs during the learning process.
