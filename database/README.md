# Database Package

This package contains all database-related code including models, configuration, and connection management.

## Structure

```
database/
├── __init__.py          # Package exports
├── models.py            # SQLAlchemy models
├── config.py            # Database configuration and connection
└── README.md            # This file
```

## Models

The following SQLAlchemy models are available:

- **Profile**: User profile information
- **OnboardingData**: User onboarding preferences
- **UserStatistics**: User learning statistics
- **UserStreaks**: User study streaks and points
- **Prompt**: AI prompt history
- **Subject**: Learning subjects
- **Topic**: Learning topics within subjects
- **Lesson**: Learning sessions
- **SessionMessage**: Messages within learning sessions
- **UserProgress**: User progress tracking

## Usage

### Importing Models

```python
from database.models import Subject, Topic
from database import Base  # For Alembic migrations
```

### Database Connection

```python
from database.config import get_db, SessionLocal

# Use in FastAPI dependencies
@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    # Use db session
    pass

# Direct usage
db = SessionLocal()
try:
    # Use db session
    pass
finally:
    db.close()
```

### Configuration

The database configuration automatically handles:
- Supabase connection (using SUPABASE_URL and SUPABASE_KEY)
- Local development fallback
- Connection pooling and optimization

## Migration

For database migrations, use Alembic:

```bash
# Generate new migration
make db-migrate

# Apply migrations
make db-upgrade

# Check current status
make db-current
```

The migrations are configured to use the models from this package.
