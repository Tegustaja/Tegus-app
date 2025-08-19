# Tegus

Unified backend (FastAPI) and frontend (Expo React Native) project.

## 🚀 Quick Start

### 1. Environment Setup

The project uses Supabase for authentication. Set up your environment variables:

```bash
# Run the interactive setup script
python3 scripts/setup_env.py

# Or manually create a .env file
cp env.example .env
# Then edit .env with your Supabase credentials
```

**Required Environment Variables:**
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Your Supabase anon key
- `EXPO_PUBLIC_SUPABASE_URL` - Same as SUPABASE_URL
- `EXPO_PUBLIC_SUPABASE_ANON_KEY` - Same as SUPABASE_KEY

### 2. Backend Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Start the backend
python3 run.py
```

The backend will be available at `http://localhost:8000`

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd tegus-frontend

# Install dependencies
npm install

# Start the development server
npm start
```

## 🔐 Authentication

The project uses Supabase authentication with:
- Email/password sign up and sign in
- JWT token management
- User profiles and admin roles
- Automatic token refresh

See [AUTHENTICATION_MIGRATION_README.md](AUTHENTICATION_MIGRATION_README.md) for detailed information.

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Test authentication system
python3 tests/test_authentication.py

# Run all tests
python3 tests/run_all_tests.py
```

## 📚 Documentation

- [Authentication Migration Guide](AUTHENTICATION_MIGRATION_README.md)
- [Environment Setup Guide](SETUP_ENVIRONMENT.md)
- [API Documentation](api/README.md)

## 🆘 Need Help?

1. Check the environment setup: `python3 scripts/setup_env.py`
2. Run tests to identify issues: `python3 tests/test_authentication.py`
3. See [SETUP_ENVIRONMENT.md](SETUP_ENVIRONMENT.md) for troubleshooting
4. Check [Supabase documentation](https://supabase.com/docs)
