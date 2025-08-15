# Admin Section for Easier Development

I've created a comprehensive admin section for the Tegus project to make development easier and more efficient. This includes both backend API endpoints and a frontend dashboard component.

## 🚀 What's Been Created

### 1. Enhanced Admin API Routes (`api/routes/admin.py`)

The existing admin routes have been significantly enhanced with:

#### Basic Admin Operations
- **Create Admin**: Create new admin accounts with 30-day privileges
- **List Admins**: View all admin accounts
- **Extend Privileges**: Extend admin privileges by specified days
- **Revoke Privileges**: Remove admin access
- **Admin Status**: Check current admin privileges and expiration

#### Development Admin Operations
- **Dashboard**: Comprehensive admin dashboard with system overview
- **System Health**: Real-time system health monitoring
- **System Statistics**: Database counts and system metrics
- **Recent Activity**: Latest users and lessons

#### User Management
- **List Users**: Paginated user listing with search
- **User Details**: Comprehensive user information including related data
- **Delete Users**: Remove users (development only)
- **Reset User Data**: Reset user progress and statistics

#### Development Utilities
- **Reset User Data**: Clear user progress for testing
- **Generate Test Data**: Trigger test data generation scripts
- **Table Info**: Get table structure and sample data

### 2. Development Utilities API (`api/routes/dev_utils.py`)

A new comprehensive development utilities route with:

#### Database Management
- **Create Backup**: Backup specific tables with or without data
- **List Backups**: View available database backups
- **Restore Backup**: Restore database from backup files
- **Backup Management**: Organize and manage backup files

#### Script Execution
- **Execute Scripts**: Safely run development scripts
- **List Scripts**: View available development scripts
- **Script Parameters**: Pass parameters to scripts
- **Timeout Control**: Prevent hanging script execution

#### Data Validation & Debugging
- **Data Integrity**: Validate table structure and relationships
- **Table Schema**: Get detailed table information
- **Data Consistency**: Check for data issues
- **Debug Tools**: Development debugging utilities

#### System Maintenance
- **Cleanup Orphaned Data**: Remove orphaned records
- **Maintenance Status**: System health recommendations
- **Data Cleanup**: Automated data maintenance

### 3. Frontend Admin Dashboard (`tegus-frontend/components/admin-dashboard.tsx`)

A React Native component providing:

#### Dashboard Overview
- System health indicators
- Real-time statistics
- Quick action buttons
- User management interface

#### Features
- **System Health**: Visual health status indicators
- **Statistics Display**: User, lesson, exercise counts
- **Quick Actions**: One-click script execution
- **User Management**: View and manage users
- **Responsive Design**: Works on mobile and web

## 🔧 How to Use

### Backend Setup

1. **Start the FastAPI server**:
   ```bash
   cd /Users/kaur/Tegus
   python3 run.py
   ```

2. **Access the admin endpoints**:
   - Dashboard: `GET /api/admin/dashboard`
   - System Health: `GET /api/admin/system-health`
   - User Management: `GET /api/admin/users`
   - Development Utils: `POST /api/dev-utils/scripts/execute`

### Frontend Integration

1. **Import the admin dashboard**:
   ```tsx
   import AdminDashboard from './components/admin-dashboard';
   ```

2. **Use in your app**:
   ```tsx
   <AdminDashboard />
   ```

### Authentication

All admin endpoints require:
- Valid JWT token in Authorization header
- Admin privileges in user profile
- Non-expired admin access

## 📊 Available Endpoints

### Admin Routes (`/api/admin/`)
- `POST /create-admin` - Create new admin
- `GET /admins` - List all admins
- `POST /extend-admin/{user_id}` - Extend admin privileges
- `DELETE /revoke-admin/{user_id}` - Revoke admin access
- `GET /admin-status` - Get current admin status
- `GET /dashboard` - Get comprehensive dashboard data
- `GET /system-health` - Get system health status
- `GET /system-stats` - Get system statistics
- `GET /users` - List users with pagination
- `GET /users/{user_id}` - Get user details
- `DELETE /users/{user_id}` - Delete user
- `POST /dev/reset-user-data/{user_id}` - Reset user data
- `POST /dev/generate-test-data` - Generate test data
- `GET /dev/table-info/{table_name}` - Get table information

### Development Utils (`/api/dev-utils/`)
- `POST /db/backup` - Create database backup
- `GET /db/backups` - List available backups
- `POST /db/restore` - Restore from backup
- `POST /scripts/execute` - Execute development scripts
- `GET /scripts/list` - List available scripts
- `POST /validate/data` - Validate data integrity
- `GET /debug/table-schema/{table_name}` - Get table schema
- `POST /maintenance/cleanup-orphaned-data` - Cleanup orphaned data
- `GET /maintenance/status` - Get maintenance status

## 🛠️ Development Scripts

The system can execute these predefined scripts:
- `create_basic_profiles` - Create test user profiles
- `generate_fake_data` - Generate comprehensive test data
- `upload_fake_data` - Upload test data to Supabase
- `check_data` - Check existing data integrity

## 🔒 Security Features

- **Admin-only access**: All endpoints require admin privileges
- **JWT authentication**: Secure token-based authentication
- **Privilege expiration**: Admin access expires automatically
- **Script whitelisting**: Only predefined scripts can be executed
- **Parameter validation**: All inputs are validated and sanitized

## 📱 Frontend Features

- **Responsive design**: Works on mobile and web
- **Real-time updates**: Live system health monitoring
- **User-friendly interface**: Intuitive admin controls
- **Error handling**: Comprehensive error messages
- **Loading states**: Visual feedback during operations

## 🚨 Important Notes

1. **Development Only**: These tools are designed for development environments
2. **Admin Access Required**: All endpoints require admin privileges
3. **Data Safety**: Backup before running destructive operations
4. **Script Execution**: Only whitelisted scripts can be executed
5. **User Management**: User deletion is permanent and cannot be undone

## 🔄 Future Enhancements

Potential improvements for the admin section:
- **Real-time monitoring**: WebSocket-based live updates
- **Advanced analytics**: Detailed usage statistics and trends
- **Automated testing**: Integration with testing frameworks
- **Performance monitoring**: System performance metrics
- **Log management**: Centralized logging and debugging
- **Backup scheduling**: Automated backup creation
- **User activity tracking**: Detailed user behavior analytics

## 📞 Support

For issues or questions about the admin section:
1. Check the API documentation at `/docs` when running the server
2. Review the endpoint responses for error details
3. Check the server logs for debugging information
4. Ensure admin privileges are properly configured

---

This admin section provides comprehensive development tools while maintaining security and following best practices. Use it to streamline your development workflow and maintain system health during development.
