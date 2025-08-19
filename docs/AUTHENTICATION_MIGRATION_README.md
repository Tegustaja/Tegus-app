# Authentication Migration to Supabase

This document describes the complete migration of the Tegus project from a custom authentication system to Supabase authentication.

## Overview

The project has been migrated to use Supabase authentication throughout the entire stack:
- **Backend**: FastAPI with Supabase client integration
- **Frontend**: React Native with direct Supabase authentication
- **Database**: Supabase PostgreSQL with RLS policies

## What Changed

### Backend Changes

1. **Centralized Supabase Client** (`api/config.py`)
   - Single Supabase client instance for all routes
   - Environment variable validation
   - Graceful fallback if Supabase is not configured

2. **Updated Authentication Routes** (`api/routes/auth.py`)
   - All auth endpoints now use Supabase directly
   - Consistent error handling
   - Proper JWT token validation
   - Profile management integration

3. **Dependencies**
   - `supabase~=2.15.0` already installed
   - `python-dotenv` for environment management

### Frontend Changes

1. **Updated Configuration** (`tegus-frontend/config/`)
   - `app.config.ts`: Uses `EXPO_PUBLIC_SUPABASE_URL` and `EXPO_PUBLIC_SUPABASE_ANON_KEY`
   - `supabase.native.ts`: Native React Native configuration
   - `supabase.web.ts`: Web configuration
   - `supabase.ts`: Main export file

2. **Authentication Service** (`tegus-frontend/services/auth-service.ts`)
   - Direct Supabase authentication calls
   - No more backend API calls for auth
   - Automatic token management
   - Profile integration

3. **Context Providers**
   - `auth-provider.tsx`: Main authentication logic
   - `supabase-provider.tsx`: Supabase client and session management
   - Route protection and navigation logic

4. **Dependencies**
   - `@supabase/supabase-js` already installed
   - `@react-native-async-storage/async-storage` for token storage

## Environment Variables

Create a `.env` file in the project root with:

```bash
# Supabase Configuration
SUPABASE_URL=your_supabase_project_url_here
SUPABASE_KEY=your_supabase_anon_key_here

# Backend Configuration
FLASK_API_KEY=your_backend_api_key_here

# Frontend Environment Variables (for Expo)
EXPO_PUBLIC_SUPABASE_URL=your_supabase_project_url_here
EXPO_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key_here
EXPO_PUBLIC_APP_NAME=Tegus
EXPO_PUBLIC_APP_SCHEME=tegus
EXPO_PUBLIC_APP_VERSION=1.0.0
EXPO_PUBLIC_BACKEND_URL=http://localhost:8000
EXPO_PUBLIC_BACKEND_API_KEY=your_backend_api_key_here
```

## Database Schema

The following tables are required in your Supabase database:

### `profiles` table
```sql
CREATE TABLE profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id),
  email TEXT,
  full_name TEXT,
  avatar_url TEXT,
  is_admin BOOLEAN DEFAULT FALSE,
  admin_expires_at TIMESTAMP WITH TIME ZONE,
  email_verified BOOLEAN DEFAULT FALSE,
  account_status TEXT DEFAULT 'active',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Other required tables
- `subjects`
- `topics`
- `lessons`
- `user_progress`
- `user_statistics`
- `user_streaks`
- `onboarding_data`

## Setup Instructions

### 1. Supabase Project Setup

1. Create a new Supabase project at [supabase.com](https://supabase.com)
2. Get your project URL and anon key from the project settings
3. Set up the database schema (see above)

### 2. Environment Configuration

1. Copy `env.example` to `.env`
2. Fill in your Supabase credentials
3. Set any additional environment variables

### 3. Backend Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Start the backend:
   ```bash
   python3 run.py
   ```

### 4. Frontend Setup

1. Install dependencies:
   ```bash
   cd tegus-frontend
   npm install
   ```

2. Start the frontend:
   ```bash
   npm start
   ```

## Testing

Run the comprehensive test suite:

```bash
python3 tests/test_authentication.py
```

This will test:
- Environment variables
- Supabase connection
- Backend API
- Database tables
- Authentication flow
- Frontend configuration

## Authentication Flow

### User Registration
1. User submits email/password/full_name
2. Supabase creates user account
3. Profile record created in `profiles` table
4. Email confirmation sent (if enabled)
5. User redirected to sign-in or protected area

### User Sign In
1. User submits email/password
2. Supabase validates credentials
3. JWT tokens generated
4. User profile fetched from database
5. User redirected to protected area

### Route Protection
- Unauthenticated users redirected to sign-in
- Authenticated users redirected away from auth pages
- Protected routes require valid JWT token

## Security Features

- JWT token validation on every protected request
- Automatic token refresh
- Secure token storage (AsyncStorage on mobile, localStorage on web)
- Row Level Security (RLS) policies in Supabase
- Admin role management with expiration dates

## Troubleshooting

### Common Issues

1. **Environment Variables Not Set**
   - Check `.env` file exists
   - Verify variable names match exactly
   - Restart your development server

2. **Supabase Connection Failed**
   - Verify URL and key are correct
   - Check Supabase project is active
   - Ensure network connectivity

3. **Database Tables Missing**
   - Run the database schema setup
   - Check table permissions
   - Verify RLS policies

4. **Frontend Build Errors**
   - Clear npm cache: `npm cache clean --force`
   - Delete node_modules and reinstall
   - Check TypeScript compilation

### Debug Mode

Enable debug logging by setting:
```bash
EXPO_PUBLIC_DEBUG=true
```

## Migration Notes

- The old custom authentication system has been completely replaced
- All existing user data should be migrated to the new `profiles` table
- JWT tokens are now managed by Supabase
- The backend still provides auth endpoints for compatibility
- Frontend now uses Supabase directly for better performance

## Support

For issues related to:
- **Supabase**: Check [Supabase documentation](https://supabase.com/docs)
- **React Native**: Check [Expo documentation](https://docs.expo.dev)
- **FastAPI**: Check [FastAPI documentation](https://fastapi.tiangolo.com)

## Future Enhancements

- Social authentication (Google, GitHub, etc.)
- Multi-factor authentication
- Advanced user roles and permissions
- Audit logging
- Rate limiting
