# Environment Setup Guide

## Quick Setup

### 1. Create Environment File

Create a `.env` file in your project root:

```bash
# Copy the example file
cp env.example .env
```

### 2. Get Your Supabase Credentials

1. Go to [supabase.com](https://supabase.com)
2. Create a new project or use existing one
3. Go to Project Settings → API
4. Copy your Project URL and anon/public key

### 3. Update Your .env File

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-key-here

# Frontend Environment Variables (for Expo)
EXPO_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co
EXPO_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-here
EXPO_PUBLIC_APP_NAME=Tegus
EXPO_PUBLIC_APP_SCHEME=tegus
EXPO_PUBLIC_APP_VERSION=1.0.0
EXPO_PUBLIC_BACKEND_URL=http://localhost:8000
EXPO_PUBLIC_BACKEND_API_KEY=your_backend_api_key_here

# Backend Configuration
FLASK_API_KEY=your_backend_api_key_here
```

### 4. Restart Your Development Server

After updating the `.env` file, restart your development server:

```bash
# Stop the current server (Ctrl+C)
# Then restart
npm start  # or expo start
```

## Troubleshooting

### "Environment variables not found" Error

1. **Check file location**: Make sure `.env` is in the project root (same level as `package.json`)
2. **Check file name**: It should be exactly `.env` (not `.env.txt` or similar)
3. **Restart server**: Environment variables are loaded when the server starts
4. **Check format**: No spaces around `=` sign, no quotes around values

### "Invalid Supabase URL" Error

1. **Check URL format**: Should be `https://your-project-id.supabase.co`
2. **No trailing slash**: Remove any trailing `/` from the URL
3. **Check project status**: Make sure your Supabase project is active

### "Invalid API Key" Error

1. **Use anon key**: Use the `anon` key, not the `service_role` key
2. **Check key length**: Should be a long string starting with `eyJ...`
3. **Copy correctly**: Make sure you copied the entire key without extra spaces

## Development vs Production

### Development
- Use `.env` file for local development
- Variables are loaded automatically
- No need to rebuild the app

### Production
- Set environment variables in your hosting platform
- For Expo builds, use `expo build:configure`
- For web builds, set in your hosting provider

## Testing Configuration

Run the test suite to verify your setup:

```bash
python3 tests/test_authentication.py
```

This will check:
- Environment variables are set
- Supabase connection works
- Backend API is accessible
- Database tables exist

## Example Working Configuration

```bash
SUPABASE_URL=https://abcdefghijklmnop.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFiY2RlZmdoaWprbG1ub3AiLCJyb2xlIjoiYW5vbiIsImlhdCI6MTYzNjU2NzI5MCwiZXhwIjoxOTUyMTQzMjkwfQ.example_key_here
EXPO_PUBLIC_SUPABASE_URL=https://abcdefghijklmnop.supabase.co
EXPO_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFiY2RlZmdoaWprbG1ub3AiLCJyb2xlIjoiYW5vbiIsImlhdCI6MTYzNjU2NzI5MCwiZXhwIjoxOTUyMTQzMjkwfQ.example_key_here
```

## Need Help?

1. Check the [Supabase documentation](https://supabase.com/docs)
2. Verify your project settings in the Supabase dashboard
3. Run the test suite to identify specific issues
4. Check the console for detailed error messages
