# Tegus Admin CLI Toolkit - Usage Guide

The Tegus Admin CLI Toolkit provides a powerful command-line interface for managing admin users and performing administrative tasks. This tool makes it easy to manage the Tegus system without needing to use the web interface.

## 🚀 Quick Start

### Prerequisites
- Python 3.7+
- Required packages: `supabase`, `python-dotenv`
- Environment variables: `SUPABASE_URL`, `SUPABASE_KEY`
- Access to Supabase Dashboard for user creation

### Installation
```bash
# Install required packages
pip install supabase python-dotenv

# Make the CLI executable
chmod +x api/cli.py
```

## 📋 Available Commands

### 1. Create Admin User
Create a new admin user with specified privileges.

**Important Note:** This command creates the admin profile in the database, but you must manually create the user account in Supabase Dashboard.

```bash
# Basic usage
python3 api/cli.py create-admin --email admin@example.com --password securepass

# With full name
python3 api/cli.py create-admin --email admin@example.com --password securepass --name "John Doe"

# Custom duration (default is 30 days)
python3 api/cli.py create-admin --email admin@example.com --password securepass --name "John Doe" --days 90
```

**What this does:**
- Creates admin profile in the database with privileges
- Sets up related data (onboarding, statistics, streaks)
- Sets expiration date for admin access
- Provides instructions for creating the user account

**After running this command, you must:**
1. Go to your Supabase Dashboard
2. Navigate to Authentication > Users
3. Click "Add User"
4. Use the email and password from the CLI command
5. The user will automatically have admin privileges

### 2. List Admin Users
View all current admin users and their status.

```bash
python3 api/cli.py list-admins
```

**Output includes:**
- Email addresses
- User IDs
- Full names
- Admin status and expiration
- Days remaining for privileges

### 3. Extend Admin Privileges
Extend admin privileges for an existing user.

```bash
python3 api/cli.py extend-admin --user-id <uuid> --days 30
```

**Example:**
```bash
python3 api/cli.py extend-admin --user-id 123e4567-e89b-12d3-a456-426614174000 --days 60
```

### 4. Revoke Admin Privileges
Remove admin privileges from a user.

```bash
python3 api/cli.py revoke-admin --user-id <uuid>
```

**Example:**
```bash
python3 api/cli.py revoke-admin --user-id 123e4567-e89b-12d3-a456-426614174000
```

### 5. System Health Check
Check the health status of your Tegus system.

```bash
python3 api/cli.py system-health
```

**Checks:**
- Database connectivity
- Supabase service status
- API availability
- Timestamp of check

### 6. Database Backup
Create backups of your database tables.

```bash
# Backup with data
python3 api/cli.py backup-db --tables profiles,lessons,exercises,subjects,topics

# Backup structure only (no data)
python3 api/cli.py backup-db --tables profiles,lessons --no-data
```

**Features:**
- Creates timestamped backup files
- Saves to `backups/` directory
- Includes metadata and table information
- Handles errors gracefully

## 🔧 Advanced Usage

### Environment Setup
Create a `.env` file in your project root:

```bash
# .env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
```

**Important:** Use your **service role key** (not the anon key) for the CLI tool to work properly.

### Running from Different Directories
```bash
# From project root
python3 api/cli.py create-admin --email admin@example.com --password pass123

# From api directory
python3 cli.py create-admin --email admin@example.com --password pass123

# Using absolute path
python3 /Users/kaur/Tegus/api/cli.py create-admin --email admin@example.com --password pass123
```

### Script Integration
You can integrate the CLI into your scripts:

```bash
#!/bin/bash
# create_admin.sh

EMAIL="admin@example.com"
PASSWORD="secure_password_123"
NAME="System Administrator"

echo "Creating admin user..."
python3 api/cli.py create-admin \
    --email "$EMAIL" \
    --password "$PASSWORD" \
    --name "$NAME" \
    --days 90

if [ $? -eq 0 ]; then
    echo "Admin profile created successfully!"
    echo "Remember to create the user account in Supabase Dashboard"
else
    echo "Failed to create admin profile"
    exit 1
fi
```

## 📊 Command Examples

### Complete Admin Setup
```bash
# 1. Check system health first
python3 api/cli.py system-health

# 2. Create primary admin profile
python3 api/cli.py create-admin \
    --email "admin@tegus.com" \
    --password "SuperSecurePass123!" \
    --name "Primary Administrator" \
    --days 365

# 3. Create backup admin profile
python3 api/cli.py create-admin \
    --email "backup-admin@tegus.com" \
    --password "BackupPass456!" \
    --name "Backup Administrator" \
    --days 90

# 4. Verify admin profiles
python3 api/cli.py list-admins

# 5. Create initial backup
python3 api/cli.py backup-db --tables profiles,lessons,exercises,subjects,topics

# 6. MANUAL STEP: Create user accounts in Supabase Dashboard
echo "Now go to Supabase Dashboard > Authentication > Users and create the user accounts"
```

### Daily Operations
```bash
# Check system status
python3 api/cli.py system-health

# List current admins
python3 api/cli.py list-admins

# Create daily backup
python3 api/cli.py backup-db --tables profiles,lessons --no-data
```

### User Management
```bash
# Extend admin privileges
python3 api/cli.py extend-admin --user-id <uuid> --days 30

# Revoke admin access
python3 api/cli.py revoke-admin --user-id <uuid>
```

## 🛡️ Security Features

### Admin Privilege Expiration
- Admin privileges automatically expire after the specified duration
- Prevents permanent admin access
- Requires manual renewal for continued access

### Secure User Creation
- Passwords are handled securely through Supabase Dashboard
- Email verification is automatically enabled
- Admin status is properly tracked and audited

### Access Control
- Only users with admin privileges can perform administrative tasks
- All operations are logged and tracked
- Failed operations provide clear error messages

## 🔍 Troubleshooting

### Common Issues

#### 1. Connection Errors
```bash
❌ Failed to connect to Supabase: [Error details]
```
**Solution:** Check your environment variables and network connection

#### 2. Permission Denied
```bash
❌ User with email admin@example.com already exists in profiles
```
**Solution:** Use a different email or check existing users with `list-admins`

#### 3. Invalid User ID
```bash
❌ User <uuid> not found
```
**Solution:** Use `list-admins` to get valid user IDs

#### 4. Service Role Key Issues
If you get permission errors, ensure you're using the **service role key** from:
- Supabase Dashboard > Settings > API
- Look for "service_role" key (not "anon" key)

### Debug Mode
For more detailed error information, the CLI now includes traceback information by default.

### Environment Variable Check
```bash
# Check if environment variables are set
echo "SUPABASE_URL: $SUPABASE_URL"
echo "SUPABASE_KEY: $SUPABASE_KEY"
```

## 📁 File Structure

After using the CLI, you'll have:

```
Tegus/
├── api/
│   └── cli.py                 # CLI tool
├── backups/                   # Database backups
│   ├── cli_backup_20241201_143022.json
│   └── cli_backup_20241201_150045.json
├── .env                      # Environment variables
└── CLI_USAGE_GUIDE.md       # This guide
```

## 🔄 Automation Examples

### Cron Job for Daily Backups
```bash
# Add to crontab (crontab -e)
0 2 * * * cd /Users/kaur/Tegus && python3 api/cli.py backup-db --tables profiles,lessons,exercises,subjects,topics
```

### CI/CD Integration
```yaml
# .github/workflows/admin-setup.yml
- name: Setup Admin Profile
  run: |
    python3 api/cli.py create-admin \
      --email "ci-admin@tegus.com" \
      --password "${{ secrets.ADMIN_PASSWORD }}" \
      --name "CI Administrator" \
      --days 1
```

## 📞 Support

### Getting Help
```bash
# Show all available commands
python3 api/cli.py --help

# Show help for specific command
python3 api/cli.py create-admin --help
```

### Error Reporting
When encountering issues:
1. Check the error message for specific details
2. Verify environment variables are set correctly
3. Ensure you have the required permissions
4. Check the system health with `system-health` command
5. Look for traceback information in error messages

### Important Notes
- **User Creation**: The CLI creates admin profiles but you must manually create user accounts in Supabase Dashboard
- **Service Role Key**: Always use the service role key, not the anon key
- **Two-Step Process**: Admin setup requires both CLI (profile) and Dashboard (user account) steps

---

The Tegus Admin CLI Toolkit provides a robust, secure, and user-friendly way to manage your Tegus system from the command line. Use it to streamline your administrative tasks and maintain system security.
