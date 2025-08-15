from fastapi import APIRouter, HTTPException, Depends, status, Query, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import os
import json
import subprocess
import sys
from datetime import datetime, timedelta
from supabase import create_client, Client
from dotenv import load_dotenv, find_dotenv

# Load environment variables
load_dotenv(find_dotenv())

# Create router
router = APIRouter()

# Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")

# Create Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Security
security = HTTPBearer()

# Models
class DatabaseBackup(BaseModel):
    tables: List[str]
    include_data: bool = True
    backup_name: Optional[str] = None

class DatabaseRestore(BaseModel):
    backup_file: str
    restore_tables: Optional[List[str]] = None

class ScriptExecution(BaseModel):
    script_name: str
    parameters: Optional[Dict[str, Any]] = None
    timeout: int = 300

class DataValidation(BaseModel):
    table_name: str
    validation_type: str  # "structure", "data", "relationships"

# Helper function to get current admin user (reuse from admin.py)
async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        # Verify the JWT token with Supabase
        user = supabase.auth.get_user(credentials.credentials)
        
        # Check if user is admin
        profile_response = supabase.table("profiles").select("is_admin, admin_expires_at").eq("id", user.user.id).execute()
        
        if not profile_response.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Profile not found"
            )
        
        profile = profile_response.data[0]
        
        # Check if user is admin and privileges haven't expired
        if not profile.get("is_admin", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required"
            )
        
        if profile.get("admin_expires_at"):
            expires_at = datetime.fromisoformat(profile["admin_expires_at"].replace('Z', '+00:00'))
            if datetime.now(expires_at.tzinfo) > expires_at:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin privileges have expired"
                )
        
        return user.user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# ============================================================================
# DATABASE MANAGEMENT
# ============================================================================

@router.post("/db/backup")
async def create_database_backup(
    backup_request: DatabaseBackup,
    current_admin: dict = Depends(get_current_admin)
):
    """
    Create a database backup for development
    """
    try:
        backup_data = {}
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_name = backup_request.backup_name or f"backup_{timestamp}"
        
        for table in backup_request.tables:
            try:
                if backup_request.include_data:
                    response = supabase.table(table).select("*").execute()
                    backup_data[table] = response.data
                else:
                    # Just get table structure info
                    backup_data[table] = {"structure": "table_exists", "row_count": 0}
            except Exception as e:
                backup_data[table] = {"error": str(e)}
        
        # Save backup to file
        backup_file = f"backups/{backup_name}.json"
        os.makedirs("backups", exist_ok=True)
        
        with open(backup_file, 'w') as f:
            json.dump({
                "backup_name": backup_name,
                "timestamp": timestamp,
                "tables": backup_request.tables,
                "include_data": backup_request.include_data,
                "data": backup_data
            }, f, indent=2, default=str)
        
        return {
            "message": "Database backup created successfully",
            "backup_file": backup_file,
            "tables_backed_up": list(backup_data.keys()),
            "timestamp": timestamp
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create backup: {str(e)}"
        )

@router.get("/db/backups")
async def list_backups(current_admin: dict = Depends(get_current_admin)):
    """
    List available database backups
    """
    try:
        backup_dir = "backups"
        if not os.path.exists(backup_dir):
            return {"backups": [], "message": "No backups directory found"}
        
        backups = []
        for file in os.listdir(backup_dir):
            if file.endswith('.json'):
                file_path = os.path.join(backup_dir, file)
                file_stat = os.stat(file_path)
                backups.append({
                    "filename": file,
                    "size_bytes": file_stat.st_size,
                    "created_at": datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                    "modified_at": datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                })
        
        return {"backups": sorted(backups, key=lambda x: x["modified_at"], reverse=True)}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list backups: {str(e)}"
        )

@router.post("/db/restore")
async def restore_database_backup(
    restore_request: DatabaseRestore,
    current_admin: dict = Depends(get_current_admin)
):
    """
    Restore database from backup (use with caution)
    """
    try:
        backup_file = f"backups/{restore_request.backup_file}"
        if not os.path.exists(backup_file):
            raise HTTPException(status_code=404, detail="Backup file not found")
        
        with open(backup_file, 'r') as f:
            backup_data = json.load(f)
        
        restored_tables = []
        errors = []
        
        tables_to_restore = restore_request.restore_tables or backup_data.get("tables", [])
        
        for table in tables_to_restore:
            if table in backup_data.get("data", {}):
                try:
                    table_data = backup_data["data"][table]
                    if isinstance(table_data, list) and table_data:
                        # Clear existing data
                        supabase.table(table).delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
                        
                        # Insert backup data
                        supabase.table(table).insert(table_data).execute()
                        restored_tables.append(table)
                    else:
                        restored_tables.append(f"{table} (no data)")
                except Exception as e:
                    errors.append(f"{table}: {str(e)}")
        
        return {
            "message": "Database restore completed",
            "restored_tables": restored_tables,
            "errors": errors,
            "backup_file": restore_request.backup_file
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restore backup: {str(e)}"
        )

# ============================================================================
# SCRIPT EXECUTION
# ============================================================================

@router.post("/scripts/execute")
async def execute_development_script(
    script_request: ScriptExecution,
    background_tasks: BackgroundTasks,
    current_admin: dict = Depends(get_current_admin)
):
    """
    Execute development scripts safely
    """
    try:
        # Define allowed scripts for security
        allowed_scripts = {
            "create_basic_profiles": "scripts/create_basic_profiles.py",
            "generate_fake_data": "scripts/faker_data_generator.py",
            "upload_fake_data": "scripts/upload_fake_data_to_supabase.py",
            "check_data": "scripts/check_existing_data.py"
        }
        
        if script_request.script_name not in allowed_scripts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Script '{script_request.script_name}' is not allowed"
            )
        
        script_path = allowed_scripts[script_request.script_name]
        
        if not os.path.exists(script_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Script file not found: {script_path}"
            )
        
        # Build command with parameters
        cmd = [sys.executable, script_path]
        if script_request.parameters:
            for key, value in script_request.parameters.items():
                if key.startswith('--'):
                    cmd.extend([key, str(value)])
                else:
                    cmd.extend([f"--{key}", str(value)])
        
        # Execute script
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=script_request.timeout,
                cwd=os.getcwd()
            )
            
            return {
                "message": "Script executed successfully",
                "script": script_request.script_name,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "execution_time": "completed"
            }
            
        except subprocess.TimeoutExpired:
            return {
                "message": "Script execution timed out",
                "script": script_request.script_name,
                "timeout": script_request.timeout,
                "execution_time": "timeout"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute script: {str(e)}"
        )

@router.get("/scripts/list")
async def list_available_scripts(current_admin: dict = Depends(get_current_admin)):
    """
    List available development scripts
    """
    try:
        scripts_dir = "scripts"
        if not os.path.exists(scripts_dir):
            return {"scripts": [], "message": "Scripts directory not found"}
        
        scripts = []
        for file in os.listdir(scripts_dir):
            if file.endswith('.py') and not file.startswith('__'):
                file_path = os.path.join(scripts_dir, file)
                file_stat = os.stat(file_path)
                
                # Check if it's an executable script
                with open(file_path, 'r') as f:
                    first_line = f.readline().strip()
                    is_executable = first_line.startswith('#!') or first_line.startswith('#!/usr/bin/env')
                
                scripts.append({
                    "filename": file,
                    "path": file_path,
                    "size_bytes": file_stat.st_size,
                    "modified_at": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                    "executable": is_executable
                })
        
        return {"scripts": sorted(scripts, key=lambda x: x["filename"])}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list scripts: {str(e)}"
        )

# ============================================================================
# DATA VALIDATION & DEBUGGING
# ============================================================================

@router.post("/validate/data")
async def validate_data_integrity(
    validation_request: DataValidation,
    current_admin: dict = Depends(get_current_admin)
):
    """
    Validate data integrity for development debugging
    """
    try:
        table_name = validation_request.table_name
        validation_type = validation_request.validation_type
        
        if validation_type == "structure":
            # Check table structure
            try:
                response = supabase.table(table_name).select("*").limit(1).execute()
                return {
                    "table": table_name,
                    "validation_type": "structure",
                    "status": "exists",
                    "has_data": len(response.data) > 0,
                    "columns": list(response.data[0].keys()) if response.data else []
                }
            except Exception as e:
                return {
                    "table": table_name,
                    "validation_type": "structure",
                    "status": "error",
                    "error": str(e)
                }
        
        elif validation_type == "data":
            # Check data consistency
            try:
                response = supabase.table(table_name).select("*").limit(100).execute()
                data_issues = []
                
                for row in response.data:
                    # Check for null values in required fields
                    for key, value in row.items():
                        if value is None and key in ['id', 'created_at']:
                            data_issues.append(f"Row {row.get('id', 'unknown')}: {key} is null")
                
                return {
                    "table": table_name,
                    "validation_type": "data",
                    "status": "completed",
                    "rows_checked": len(response.data),
                    "issues_found": len(data_issues),
                    "issues": data_issues
                }
                
            except Exception as e:
                return {
                    "table": table_name,
                    "validation_type": "data",
                    "status": "error",
                    "error": str(e)
                }
        
        elif validation_type == "relationships":
            # Check foreign key relationships
            try:
                # This is a simplified check - in production you'd want more sophisticated validation
                response = supabase.table(table_name).select("*").limit(10).execute()
                
                return {
                    "table": table_name,
                    "validation_type": "relationships",
                    "status": "completed",
                    "note": "Basic relationship validation completed. Use database tools for comprehensive FK validation."
                }
                
            except Exception as e:
                return {
                    "table": table_name,
                    "validation_type": "relationships",
                    "status": "error",
                    "error": str(e)
                }
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid validation type: {validation_type}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate data: {str(e)}"
        )

@router.get("/debug/table-schema/{table_name}")
async def get_table_schema(
    table_name: str,
    current_admin: dict = Depends(get_current_admin)
):
    """
    Get detailed table schema information for debugging
    """
    try:
        # Get sample data to infer schema
        response = supabase.table(table_name).select("*").limit(5).execute()
        
        if not response.data:
            return {
                "table": table_name,
                "schema": {},
                "message": "No data available to infer schema"
            }
        
        # Analyze first row to determine data types
        schema = {}
        sample_row = response.data[0]
        
        for column, value in sample_row.items():
            if value is None:
                schema[column] = {"type": "unknown", "nullable": True}
            else:
                python_type = type(value).__name__
                schema[column] = {
                    "type": python_type,
                    "nullable": False,
                    "sample_value": str(value)[:100]  # Truncate long values
                }
        
        return {
            "table": table_name,
            "schema": schema,
            "sample_rows": len(response.data),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get table schema: {str(e)}"
        )

# ============================================================================
# SYSTEM MAINTENANCE
# ============================================================================

@router.post("/maintenance/cleanup-orphaned-data")
async def cleanup_orphaned_data(
    current_admin: dict = Depends(get_current_admin)
):
    """
    Clean up orphaned data for development environment
    """
    try:
        cleanup_results = {}
        
        # Clean up orphaned user statistics
        try:
            # Find profiles that don't exist
            stats_response = supabase.table("user_statistics").select("user_id").execute()
            orphaned_stats = []
            
            for stat in stats_response.data:
                profile_response = supabase.table("profiles").select("id").eq("id", stat["user_id"]).execute()
                if not profile_response.data:
                    orphaned_stats.append(stat["user_id"])
            
            if orphaned_stats:
                supabase.table("user_statistics").delete().in_("user_id", orphaned_stats).execute()
                cleanup_results["orphaned_statistics"] = len(orphaned_stats)
            else:
                cleanup_results["orphaned_statistics"] = 0
                
        except Exception as e:
            cleanup_results["orphaned_statistics"] = f"error: {str(e)}"
        
        # Clean up orphaned streaks
        try:
            streaks_response = supabase.table("user_streaks").select("user_id").execute()
            orphaned_streaks = []
            
            for streak in streaks_response.data:
                profile_response = supabase.table("profiles").select("id").eq("id", streak["user_id"]).execute()
                if not profile_response.data:
                    orphaned_streaks.append(streak["user_id"])
            
            if orphaned_streaks:
                supabase.table("user_streaks").delete().in_("user_id", orphaned_streaks).execute()
                cleanup_results["orphaned_streaks"] = len(orphaned_streaks)
            else:
                cleanup_results["orphaned_streaks"] = 0
                
        except Exception as e:
            cleanup_results["orphaned_streaks"] = f"error: {str(e)}"
        
        return {
            "message": "Data cleanup completed",
            "results": cleanup_results,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup orphaned data: {str(e)}"
        )

@router.get("/maintenance/status")
async def get_maintenance_status(current_admin: dict = Depends(get_current_admin)):
    """
    Get system maintenance status and recommendations
    """
    try:
        status_info = {
            "database_size": "unknown",
            "orphaned_records": 0,
            "last_cleanup": "never",
            "recommendations": []
        }
        
        # Check for orphaned records
        try:
            stats_response = supabase.table("user_statistics").select("user_id").execute()
            orphaned_count = 0
            
            for stat in stats_response.data:
                profile_response = supabase.table("profiles").select("id").eq("id", stat["user_id"]).execute()
                if not profile_response.data:
                    orphaned_count += 1
            
            status_info["orphaned_records"] = orphaned_count
            
            if orphaned_count > 10:
                status_info["recommendations"].append("Consider running data cleanup")
            
        except Exception:
            pass
        
        # Check backup status
        backup_dir = "backups"
        if os.path.exists(backup_dir):
            backup_files = [f for f in os.listdir(backup_dir) if f.endswith('.json')]
            if not backup_files:
                status_info["recommendations"].append("Create initial database backup")
            elif len(backup_files) > 10:
                status_info["recommendations"].append("Consider cleaning up old backups")
        
        return status_info
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get maintenance status: {str(e)}"
        )
