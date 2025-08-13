# Database Migrations with Alembic

This directory contains database migration scripts for the Tegus project using Alembic.

## 🚀 **Quick Start**

### **1. Install Dependencies**
```bash
make install
# or manually:
pip install alembic sqlalchemy psycopg2-binary
```

### **2. Initialize Alembic (First Time Only)**
```bash
make db-init
```

### **3. Create Your First Migration**
```bash
make db-migrate message="Initial database schema"
```

### **4. Apply Migrations**
```bash
make db-upgrade
```

## 📋 **Available Commands**

| Command | Description | Usage |
|---------|-------------|-------|
| `make db-migrate message="Description"` | Create new migration | `make db-migrate message="Add user table"` |
| `make db-upgrade` | Apply all pending migrations | `make db-upgrade` |
| `make db-downgrade` | Rollback last migration | `make db-downgrade` |
| `make db-current` | Show current migration version | `make db-current` |
| `make db-history` | Show migration history | `make db-history` |
| `make db-show revision` | Show migration details | `make db-show 001` |

## 🔧 **Manual Alembic Commands**

If you prefer to use Alembic directly:

```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1

# Check status
alembic current
alembic history
```

## 📁 **Directory Structure**

```
migrations/
├── env.py              # Alembic environment configuration
├── script.py.mako      # Migration script template
├── versions/           # Migration files
│   ├── 001_initial_schema.py
│   └── ...
└── README.md           # This file
```

## 🗄️ **Database Models**

The migrations are based on SQLAlchemy models defined in `app/models.py`:

- **Profile** - User profile information
- **OnboardingData** - User preferences and goals
- **UserStatistics** - Learning progress metrics
- **UserStreaks** - Gamification data
- **Lesson** - Learning sessions with step tracking
- **SessionMessage** - Chat messages within lesson sessions
- **UserProgress** - User progress tracking per topic
- **Prompt** - User prompts and responses
- **Subject** - Learning subjects with metadata
- **Topic** - Topics within subjects with ordering and locking

## ⚙️ **Configuration**

### **Environment Variables**

The migration system uses these environment variables:

- `DATABASE_URL` - Direct database connection string (optional)
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_KEY` - Supabase API key

### **Database Connection**

The system automatically builds the database URL from your Supabase credentials:

```
postgresql://postgres:SUPABASE_KEY@PROJECT_ID.supabase.co:5432/postgres
```

## 🚨 **Important Notes**

1. **Always backup your database** before running migrations
2. **Test migrations** in development before production
3. **Review generated migrations** before applying them
4. **Never modify existing migration files** - create new ones instead

## 🔍 **Troubleshooting**

### **Common Issues**

1. **Connection Errors**: Check your Supabase credentials
2. **Import Errors**: Ensure `database.models` can be imported
3. **Permission Errors**: Verify database user permissions

### **Reset Migrations**

If you need to start fresh:

```bash
# Remove existing migrations
rm -rf migrations/versions/*

# Recreate initial migration
make db-migrate message="Initial schema"
```

## 📚 **Resources**

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Supabase Documentation](https://supabase.com/docs)
