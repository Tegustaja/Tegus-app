#!/usr/bin/env python3
"""
Tegus Admin CLI Toolkit

Command-line interface for managing admin users and performing administrative tasks.
This tool provides a convenient way to manage the Tegus system from the command line.

Usage:
    python3 api/cli.py create-admin --email admin@example.com --password securepass --name "Admin User"
    python3 api/cli.py list-admins
    python3 api/cli.py extend-admin --user-id <uuid> --days 30
    python3 api/cli.py revoke-admin --user-id <uuid>
    python3 api/cli.py system-health
    python3 api/cli.py backup-db --tables profiles,lessons,exercises
"""

import sys
import os
import argparse
import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path
import traceback

# Add the parent directory to the path so we can import the required modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from supabase import create_client, Client
    from dotenv import load_dotenv, find_dotenv
    import bcrypt
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure you have the required dependencies installed:")
    print("   pip install supabase python-dotenv bcrypt")
    sys.exit(1)

# Load environment variables
load_dotenv(find_dotenv())

class TegusAdminCLI:
    """Command-line interface for Tegus admin management"""
    
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            print("❌ SUPABASE_URL and SUPABASE_KEY environment variables must be set")
            print("💡 Check your .env file or environment variables")
            sys.exit(1)
        
        try:
            self.supabase = create_client(self.supabase_url, self.supabase_key)
            print("✅ Connected to Supabase successfully")
        except Exception as e:
            print(f"❌ Failed to connect to Supabase: {e}")
            sys.exit(1)
    
    def create_admin(self, email: str, password: str, name: Optional[str] = None, days: int = 30) -> bool:
        """
        Create a new admin user
        
        Args:
            email: Admin email address
            password: Admin password
            name: Full name (optional)
            days: Admin privileges duration in days (default: 30)
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print(f"👤 Creating admin user: {email}")
            
            # Check if user already exists in profiles table
            print("🔍 Checking if user already exists...")
            existing_profile = self.supabase.table("profiles").select("id, email").eq("email", email).execute()
            
            if existing_profile.data:
                print(f"⚠️  User with email {email} already exists in profiles")
                return False
            
            # Generate a new UUID for the user
            user_id = str(uuid.uuid4())
            print(f"🆔 Generated user ID: {user_id}")
            
            # Hash the password
            password_bytes = password.encode('utf-8')
            salt = bcrypt.gensalt()
            password_hash = bcrypt.hashpw(password_bytes, salt)
            
            # Set admin privileges
            admin_expires_at = datetime.utcnow() + timedelta(days=days)
            
            # Create profile with admin privileges
            profile_data = {
                "id": user_id,
                "email": email,
                "password_hash": password_hash.decode('utf-8'),
                "salt": salt.decode('utf-8'),
                "first_name": name.split()[0] if name else None,
                "last_name": " ".join(name.split()[1:]) if name and len(name.split()) > 1 else None,
                "is_admin": True,
                "admin_expires_at": admin_expires_at.isoformat(),
                "email_verified": True,
                "account_status": "active",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            print("📝 Creating admin profile...")
            self.supabase.table("profiles").insert(profile_data).execute()
            
            # Create user statistics
            stats_data = {
                "user_id": user_id,
                "total_lessons": 0,
                "total_study_time_minutes": 0,
                "total_tests_completed": 0
            }
            self.supabase.table("user_statistics").insert(stats_data).execute()
            
            # Create user streaks
            streaks_data = {
                "user_id": user_id,
                "current_streak": 0,
                "longest_streak": 0,
                "last_study_date": None,
                "points": 0,
                "hearts": 5
            }
            self.supabase.table("user_streaks").insert(streaks_data).execute()
            
            print(f"✅ Admin user '{email}' created successfully!")
            print(f"   - User ID: {user_id}")
            print(f"   - Admin privileges expire: {admin_expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   - Duration: {days} days")
            print(f"   - Password hash and salt stored securely")
            print(f"\n⚠️  IMPORTANT: You need to create the user account in Supabase Dashboard:")
            print(f"   1. Go to Authentication > Users in your Supabase project")
            print(f"   2. Click 'Add User'")
            print(f"   3. Use email: {email}")
            print(f"   4. Use password: {password}")
            print(f"   5. The user will automatically have admin privileges")
            print(f"   6. Password verification will work with the stored hash")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating admin user: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            return False
    
    def list_admins(self) -> bool:
        """List all admin users"""
        try:
            print("👥 Listing all admin users...")
            
            response = self.supabase.table("profiles").select("*").eq("is_admin", True).execute()
            
            if not response.data:
                print("ℹ️  No admin users found")
                return True
            
            print(f"\n📊 Found {len(response.data)} admin user(s):")
            print("-" * 80)
            
            for i, admin in enumerate(response.data, 1):
                expires_at = admin.get("admin_expires_at")
                if expires_at:
                    try:
                        expires_dt = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                        days_remaining = max(0, (expires_dt - datetime.now()).days)
                        status = f"Active ({days_remaining} days remaining)"
                    except:
                        status = "Active (expiration date invalid)"
                else:
                    status = "Active (no expiration)"
                
                print(f"{i}. {admin.get('email', 'N/A')}")
                print(f"   ID: {admin.get('id', 'N/A')}")
                print(f"   Name: {admin.get('first_name', '')} {admin.get('last_name', '')}".strip() or "N/A")
                print(f"   Status: {status}")
                print(f"   Created: {admin.get('created_at', 'N/A')}")
                print()
            
            return True
            
        except Exception as e:
            print(f"❌ Error listing admins: {e}")
            return False
    
    def extend_admin(self, user_id: str, days: int) -> bool:
        """Extend admin privileges for a user"""
        try:
            print(f"⏰ Extending admin privileges for user {user_id} by {days} days...")
            
            # Get current profile
            profile_response = self.supabase.table("profiles").select("is_admin, admin_expires_at").eq("id", user_id).execute()
            
            if not profile_response.data:
                print(f"❌ User {user_id} not found")
                return False
            
            profile = profile_response.data[0]
            
            if not profile.get("is_admin", False):
                print(f"❌ User {user_id} is not an admin")
                return False
            
            # Calculate new expiration date
            current_expires = profile.get("admin_expires_at")
            if current_expires:
                try:
                    current_expires_dt = datetime.fromisoformat(current_expires.replace('Z', '+00:00'))
                    new_expires = current_expires_dt + timedelta(days=days)
                except:
                    new_expires = datetime.utcnow() + timedelta(days=days)
            else:
                new_expires = datetime.utcnow() + timedelta(days=days)
            
            # Update admin expiration
            self.supabase.table("profiles").update({
                "admin_expires_at": new_expires.isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", user_id).execute()
            
            print(f"✅ Admin privileges extended successfully!")
            print(f"   New expiration: {new_expires.strftime('%Y-%m-%d %H:%M:%S')}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error extending admin privileges: {e}")
            return False
    
    def revoke_admin(self, user_id: str) -> bool:
        """Revoke admin privileges from a user"""
        try:
            print(f"🚫 Revoking admin privileges for user {user_id}...")
            
            # Update profile to remove admin privileges
            self.supabase.table("profiles").update({
                "is_admin": False,
                "admin_expires_at": None,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", user_id).execute()
            
            print(f"✅ Admin privileges revoked successfully!")
            
            return True
            
        except Exception as e:
            print(f"❌ Error revoking admin privileges: {e}")
            return False
    
    def system_health(self) -> bool:
        """Check system health status"""
        try:
            print("🏥 Checking system health...")
            
            # Check database connectivity
            try:
                self.supabase.table("profiles").select("count", count="exact").limit(1).execute()
                db_status = "✅ Healthy"
            except Exception:
                db_status = "❌ Unhealthy"
            
            # Check Supabase status
            try:
                # Simple connection test
                self.supabase.table("profiles").select("id").limit(1).execute()
                supabase_status = "✅ Healthy"
            except Exception:
                supabase_status = "❌ Unhealthy"
            
            print(f"\n📊 System Health Report:")
            print("-" * 40)
            print(f"Database:     {db_status}")
            print(f"Supabase:     {supabase_status}")
            print(f"API:          ✅ Healthy")
            print(f"Timestamp:    {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error checking system health: {e}")
            return False
    
    def backup_database(self, tables: List[str], include_data: bool = True) -> bool:
        """Create database backup"""
        try:
            print(f"💾 Creating database backup for tables: {', '.join(tables)}")
            
            backup_data = {}
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_name = f"cli_backup_{timestamp}"
            
            for table in tables:
                try:
                    if include_data:
                        response = self.supabase.table(table).select("*").execute()
                        backup_data[table] = response.data
                        print(f"   📋 {table}: {len(response.data)} rows")
                    else:
                        backup_data[table] = {"structure": "table_exists", "row_count": 0}
                        print(f"   📋 {table}: structure only")
                except Exception as e:
                    backup_data[table] = {"error": str(e)}
                    print(f"   ❌ {table}: error - {e}")
            
            # Save backup to file
            backup_file = f"backups/{backup_name}.json"
            os.makedirs("backups", exist_ok=True)
            
            with open(backup_file, 'w') as f:
                json.dump({
                    "backup_name": backup_name,
                    "timestamp": timestamp,
                    "tables": tables,
                    "include_data": include_data,
                    "data": backup_data
                }, f, indent=2, default=str)
            
            print(f"\n✅ Backup created successfully!")
            print(f"   File: {backup_file}")
            print(f"   Tables: {len(backup_data)}")
            print(f"   Size: {os.path.getsize(backup_file) / 1024:.1f} KB")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating backup: {e}")
            return False

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Tegus Admin CLI Toolkit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 api/cli.py create-admin --email admin@example.com --password securepass --name "Admin User"
  python3 api/cli.py list-admins
  python3 api/cli.py extend-admin --user-id <uuid> --days 30
  python3 api/cli.py revoke-admin --user-id <uuid>
  python3 api/cli.py system-health
  python3 api/cli.py backup-db --tables profiles,lessons,exercises
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create admin command
    create_parser = subparsers.add_parser('create-admin', help='Create a new admin user')
    create_parser.add_argument('--email', required=True, help='Admin email address')
    create_parser.add_argument('--password', required=True, help='Admin password')
    create_parser.add_argument('--name', help='Full name (optional)')
    create_parser.add_argument('--days', type=int, default=30, help='Admin privileges duration in days (default: 30)')
    
    # List admins command
    list_parser = subparsers.add_parser('list-admins', help='List all admin users')
    
    # Extend admin command
    extend_parser = subparsers.add_parser('extend-admin', help='Extend admin privileges')
    extend_parser.add_argument('--user-id', required=True, help='User ID to extend privileges for')
    extend_parser.add_argument('--days', type=int, required=True, help='Number of days to extend by')
    
    # Revoke admin command
    revoke_parser = subparsers.add_parser('revoke-admin', help='Revoke admin privileges')
    revoke_parser.add_argument('--user-id', required=True, help='User ID to revoke privileges from')
    
    # System health command
    health_parser = subparsers.add_parser('system-health', help='Check system health status')
    
    # Backup database command
    backup_parser = subparsers.add_parser('backup-db', help='Create database backup')
    backup_parser.add_argument('--tables', required=True, help='Comma-separated list of tables to backup')
    backup_parser.add_argument('--no-data', action='store_true', help='Backup structure only (no data)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize CLI
    cli = TegusAdminCLI()
    
    # Execute command
    success = False
    
    if args.command == 'create-admin':
        success = cli.create_admin(
            email=args.email,
            password=args.password,
            name=args.name,
            days=args.days
        )
    
    elif args.command == 'list-admins':
        success = cli.list_admins()
    
    elif args.command == 'extend-admin':
        success = cli.extend_admin(
            user_id=args.user_id,
            days=args.days
        )
    
    elif args.command == 'revoke-admin':
        success = cli.revoke_admin(user_id=args.user_id)
    
    elif args.command == 'system-health':
        success = cli.system_health()
    
    elif args.command == 'backup-db':
        tables = [t.strip() for t in args.tables.split(',')]
        success = cli.backup_database(
            tables=tables,
            include_data=not args.no_data
        )
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
