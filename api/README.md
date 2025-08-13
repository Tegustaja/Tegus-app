# Tegus API

This directory contains all FastAPI route definitions and API-related code for the Tegus project.

## Structure

- `__init__.py` - Package initialization
- `config.py` - API configuration and environment variables
- `routes/` - Route definitions organized by feature
  - `__init__.py` - Routes package initialization
  - `routes.py` - Main application routes
  - `auth.py` - Authentication and user management routes
  - `subjects.py` - Subject and topic management routes
  - `lessons.py` - Lesson session management routes
  - `exercises.py` - Exercise generation and answer checking routes
  - `quizzes.py` - Quiz generation and answer submission routes
  - `progress.py` - User progress tracking and analytics routes
  - `content.py` - Content management and learning materials routes
  - `settings.py` - User settings and preferences management routes
- `README.md` - This documentation file

## API Endpoints

All endpoints are prefixed with `/api` when accessed from the main application.

### Authentication Routes (`/api/auth`)

- **`POST /api/auth/sign-up`** - User registration with onboarding data
- **`POST /api/auth/sign-in`** - User authentication
- **`GET /api/auth/profile`** - Get current user profile (requires auth)
- **`PUT /api/auth/profile`** - Update user profile (requires auth)
- **`POST /api/auth/sign-out`** - Sign out user (requires auth)
- **`POST /api/auth/refresh`** - Refresh access token

### Subject & Topic Management Routes (`/api/subjects`)

- **`GET /api/subjects`** - Fetch all subjects
- **`GET /api/subjects/{id}`** - Get specific subject by ID
- **`GET /api/subjects/{id}/topics`** - Get topics for a specific subject
- **`GET /api/subjects/{id}/with-topics`** - Get subject with all its topics
- **`PUT /api/subjects/{id}/unlock`** - Unlock a subject for a user
- **`GET /api/subjects/{id}/topics/{topic_id}/unlock`** - Unlock a specific topic

### Lesson Session Management Routes (`/api/lessons`)

- **`POST /api/lessons/sessions`** - Create new lesson session
- **`GET /api/lessons/sessions/{id}`** - Get lesson session details
- **`PUT /api/lessons/sessions/{id}`** - Update lesson session progress
- **`GET /api/lessons/sessions/{id}/progress`** - Get user progress for a topic
- **`GET /api/lessons/sessions/{id}/messages`** - Get all messages for a lesson session
- **`POST /api/lessons/sessions/{id}/messages`** - Add a message to a lesson session

### Exercise Generation Routes (`/api/exercises`)

- **`POST /api/exercises/generate`** - Generate calculation exercises, multiple choice, or true/false questions
- **`POST /api/exercises/check-answer`** - Check user's exercise answer
- **`GET /api/exercises/types`** - Get available exercise types
- **`GET /api/exercises/difficulties`** - Get available difficulty levels

### Quiz Generation Routes (`/api/quizzes`)

- **`POST /api/quizzes/generate`** - Generate quiz questions
- **`POST /api/quizzes/submit-answer`** - Submit and grade quiz answers
- **`GET /api/quizzes/types`** - Get available quiz types
- **`GET /api/quizzes/difficulties`** - Get available difficulty levels
- **`GET /api/quizzes/topics`** - Get available topics for quiz generation

### User Progress & Analytics Routes (`/api/progress`)

- **`GET /api/progress/{userId}`** - Get user's overall progress
- **`GET /api/progress/{userId}/topics/{topicId}`** - Get progress for specific topic
- **`PUT /api/progress/{userId}/topics/{topicId}`** - Update topic progress
- **`GET /api/progress/leaderboard`** - Get leaderboard data
- **`GET /api/progress/{userId}/activity`** - Get user activity for the last N days
- **`GET /api/progress/{userId}/streaks`** - Get detailed user streak information

### Content Management Routes (`/api/content`)

- **`GET /api/content/topics/{topicId}/materials`** - Get learning materials for a topic
- **`POST /api/content/feedback`** - Submit user feedback on content
- **`GET /api/content/recommendations`** - Get personalized content recommendations
- **`GET /api/content/materials/{materialId}`** - Get detailed material information
- **`GET /api/content/topics/{topicId}/overview`** - Get topic overview with material counts

### User Preferences & Settings Routes (`/api/settings`)

- **`GET /api/settings/{userId}`** - Get user settings
- **`PUT /api/settings/{userId}`** - Update user settings
- **`GET /api/settings/{userId}/preferences`** - Get learning preferences
- **`PUT /api/settings/{userId}/preferences`** - Update learning preferences
- **`GET /api/settings/{userId}/notifications`** - Get notification settings
- **`PUT /api/settings/{userId}/notifications`** - Update notification settings
- **`GET /api/settings/{userId}/export`** - Export all user data and settings

### Main Application Routes

- **`GET /api/`** - API index page
- **`POST /api/secure-endpoint`** - Secure endpoint requiring API key
- **`POST /api/create-plan`** - Create a new study plan
- **`POST /api/execute-step`** - Execute a specific step in a plan
- **`GET /api/health`** - Health check endpoint
- **`POST /api/rag`** - RAG (Retrieval-Augmented Generation) endpoint
- **`POST /api/teacher`** - Ask teacher questions endpoint

## Configuration

The API configuration is managed in `config.py` and includes:

- Environment variables loading
- API key configuration
- Supabase database configuration
- Logging configuration
- CORS settings

## Authentication

The API uses Supabase for authentication with JWT tokens:

1. **Sign Up**: Creates user account, profile, onboarding data, and initial statistics
2. **Sign In**: Authenticates user and returns access/refresh tokens
3. **Protected Routes**: Use `Authorization: Bearer <token>` header
4. **Token Refresh**: Use refresh token to get new access token

## Database Integration

The authentication system integrates with the existing database schema:

- `profiles` - User profile information
- `onboarding_data` - User preferences and goals
- `user_statistics` - Learning progress metrics
- `user_streaks` - Gamification data

## Usage

The routes are automatically included in the main FastAPI application (`run.py`) with the `/api` prefix. This provides a clean separation between the main application logic and the API route definitions.

## Adding New Routes

To add new routes:

1. Create a new route file in the `routes/` directory (e.g., `subjects.py`)
2. Import and include the router in `routes/routes.py`
3. The route will automatically be available at `/api/your-route-name`

## Models

All Pydantic models for request/response validation are defined in their respective route files to keep related code together.

## Dependencies

Make sure to install the required dependencies:

```bash
pip install email-validator
```

The authentication system requires:
- Supabase client configuration
- JWT token handling
- Email validation
- Password hashing (handled by Supabase) 