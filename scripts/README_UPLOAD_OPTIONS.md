# Upload Options for Personalized Learning Fake Data

This document explains the different ways you can upload the generated fake data to your Supabase database.

## Overview

We've created multiple upload methods to give you flexibility based on your setup and preferences:

1. **API Endpoint Uploader** - Uses the FastAPI endpoints (recommended for testing)
2. **Direct Database Uploader** - Connects directly to Supabase (faster for bulk uploads)
3. **Manual SQL Upload** - Direct SQL commands for database administrators

## Prerequisites

Before uploading, make sure you have:

1. ✅ Generated fake data using one of the generators
2. ✅ Set up your Supabase database with the required tables
3. ✅ Configured your environment variables
4. ✅ Started your FastAPI server (if using API uploader)

## Option 1: API Endpoint Uploader (Recommended for Testing)

### What it does
- Uploads data through your FastAPI endpoints
- Tests the API functionality end-to-end
- Validates data through your Pydantic models
- Simulates real user interactions

### Usage

```bash
# Basic upload to localhost:8000
python3 scripts/upload_fake_data_to_supabase.py

# Upload to different API server
python3 scripts/upload_fake_data_to_supabase.py --api-url http://your-server.com

# Dry run (no actual upload)
python3 scripts/upload_fake_data_to_supabase.py --dry-run
```

### Advantages
- ✅ Tests your API endpoints
- ✅ Validates data through your models
- ✅ Simulates real usage patterns
- ✅ Easy to debug and monitor

### Disadvantages
- ❌ Slower than direct upload
- ❌ Requires API server to be running
- ❌ May hit API rate limits

## Option 2: Direct Database Uploader (Recommended for Bulk Uploads)

### What it does
- Connects directly to Supabase using the client
- Bypasses API layer for faster uploads
- Still maintains data integrity
- Better for large datasets

### Usage

```bash
# Basic upload
python3 scripts/direct_db_uploader.py

# Dry run (no actual upload)
python3 scripts/direct_db_uploader.py --dry-run
```

### Advantages
- ✅ Much faster than API uploads
- ✅ No API server required
- ✅ Better for large datasets
- ✅ Direct database control

### Disadvantages
- ❌ Bypasses API validation
- ❌ Doesn't test API endpoints
- ❌ Requires direct database access

## Option 3: Manual SQL Upload (For Database Administrators)

### What it does
- Provides SQL commands you can run directly
- Full control over the upload process
- Can be used with any database client

### Usage

1. Generate the SQL commands:
```bash
python3 scripts/generate_sql_upload.py
```

2. Run the SQL in your database client:
```sql
-- Example SQL commands
INSERT INTO lesson_parts (id, lesson_id, title, description, part_order, is_completed, created_at, updated_at)
VALUES ('uuid-here', 'lesson-uuid', 'Part 1: Introduction', 'Description here', 1, false, NOW(), NOW());
```

### Advantages
- ✅ Full control over the process
- ✅ Can be automated with scripts
- ✅ Works with any database client
- ✅ Can be version controlled

### Disadvantages
- ❌ Manual process
- ❌ No automatic error handling
- ❌ Requires SQL knowledge
- ❌ Time-consuming for large datasets

## Environment Setup

### Required Environment Variables

Create a `.env` file in your project root:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here
SUPABASE_SERVICE_KEY=your-service-key-here

# Database Configuration (if using direct connection)
DATABASE_URL=postgresql://username:password@host:port/database
```

### Install Dependencies

```bash
# For API uploader
pip install requests

# For direct database uploader
pip install supabase

# For all uploaders
pip install -r requirements.txt
```

## Upload Process

### Data Flow

```
Fake Data Generator → JSON Files → Upload Script → Database
```

### Upload Order

The uploaders follow this dependency order:

1. **Lesson Parts** (depends on Lessons)
2. **Exercises** (depends on Lesson Parts)
3. **Subtasks** (depends on Exercises)
4. **Progress Records** (depends on all entities)
5. **Extensions** (depends on Lessons)

### Progress Tracking

Each uploader provides:
- Real-time progress updates
- Success/failure counts
- Detailed error messages
- Upload results saved to files

## Troubleshooting

### Common Issues

#### 1. Connection Errors
```bash
❌ API connection failed: Connection refused
```
**Solution**: Make sure your API server is running and accessible

#### 2. Authentication Errors
```bash
❌ Failed to initialize Supabase client: Invalid API key
```
**Solution**: Check your environment variables and Supabase credentials

#### 3. Table Not Found Errors
```bash
❌ relation "lesson_parts" does not exist
```
**Solution**: Run your database migrations to create the required tables

#### 4. Foreign Key Constraint Errors
```bash
❌ insert or update on table "exercises" violates foreign key constraint
```
**Solution**: Make sure parent entities (lessons, lesson parts) exist first

### Debug Mode

Enable debug output:

```bash
# Set environment variable
export DEBUG=1

# Or run with verbose logging
python3 scripts/direct_db_uploader.py --verbose
```

### Check Upload Results

After upload, check the results:

```bash
# View upload results
cat upload_results/upload_results.json

# View updated data with new IDs
ls upload_results/updated_data/
```

## Performance Optimization

### For Large Datasets

1. **Use Direct Database Uploader** for datasets > 1000 records
2. **Adjust batch sizes** in the uploader
3. **Monitor database performance** during upload
4. **Use dry-run first** to estimate upload time

### Batch Uploading

The uploaders process records one by one by default. For better performance:

```python
# Modify the uploader to use batch inserts
def upload_batch(self, records, batch_size=100):
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        # Upload batch
```

## Security Considerations

### API Uploader
- Uses your existing API authentication
- Respects rate limits and validation
- Safe for production use

### Direct Database Uploader
- Requires database credentials
- Bypasses API security
- Use only in trusted environments

### Manual SQL Upload
- Full database access
- Requires careful validation
- Use only in development/testing

## Best Practices

### 1. Always Test First
```bash
# Run dry-run before actual upload
python3 scripts/direct_db_uploader.py --dry-run
```

### 2. Backup Your Database
```bash
# Create backup before large uploads
pg_dump your_database > backup_before_upload.sql
```

### 3. Monitor Upload Progress
- Watch the console output
- Check upload results files
- Monitor database performance

### 4. Validate Data After Upload
```bash
# Check data integrity
python3 scripts/validate_uploaded_data.py
```

## Example Workflows

### Development Testing
```bash
# 1. Generate small test dataset
python3 scripts/simple_fake_data_generator.py

# 2. Upload via API (tests endpoints)
python3 scripts/upload_fake_data_to_supabase.py --dry-run

# 3. Upload for real
python3 scripts/upload_fake_data_to_supabase.py
```

### Production Setup
```bash
# 1. Generate comprehensive dataset
python3 scripts/generate_fake_personalized_data.py --count 100 --save

# 2. Upload directly to database (faster)
python3 scripts/direct_db_uploader.py

# 3. Verify upload results
python3 scripts/validate_uploaded_data.py
```

### Bulk Data Migration
```bash
# 1. Generate large dataset
python3 scripts/generate_fake_personalized_data.py --count 1000 --save

# 2. Use direct uploader for speed
python3 scripts/direct_db_uploader.py

# 3. Check for any failed uploads
cat upload_results/direct_upload_results.json
```

## Monitoring and Maintenance

### Upload Logs
- All uploads are logged to `upload_results/` directory
- Failed uploads are tracked with error details
- Success counts are provided for verification

### Data Validation
- Check foreign key relationships
- Verify data integrity
- Monitor database performance

### Cleanup
```bash
# Remove temporary files
rm -rf fake_data/
rm -rf upload_results/

# Or keep for reference
mv fake_data/ fake_data_backup/
mv upload_results/ upload_results_backup/
```

## Support and Troubleshooting

### Getting Help

1. **Check the logs** in `upload_results/` directory
2. **Verify environment variables** are set correctly
3. **Test database connection** manually
4. **Use dry-run mode** to identify issues

### Common Commands

```bash
# Test API connection
curl http://localhost:8000/docs

# Test database connection
python3 -c "from database.config import get_supabase_client; print('Connected')"

# Check generated data
ls -la fake_data/

# View upload results
cat upload_results/*.json
```

## Conclusion

Choose the upload method that best fits your needs:

- **API Uploader**: For testing and validation
- **Direct Uploader**: For speed and bulk operations
- **Manual SQL**: For full control and automation

All methods will successfully populate your database with realistic test data for the personalized learning system. Start with a dry-run to ensure everything is configured correctly before proceeding with the actual upload.
