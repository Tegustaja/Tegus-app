# Fake Data Generators for Personalized Learning API

This directory contains fake data generators for testing the personalized learning lesson structure API endpoints.

## Overview

The fake data generators create realistic test data for:
- **Lessons** - Main learning sessions
- **Lesson Parts** - Individual sections within lessons
- **Exercises** - Learning activities and questions
- **Subtasks** - Optional additional content under exercises
- **Progress Tracking** - User progress at every level
- **Lesson Extensions** - Additional content added during learning

## Available Generators

### 1. Comprehensive Generator (`generate_fake_personalized_data.py`)

**Features:**
- Generates realistic, varied content with proper relationships
- Uses templates for exercise and subtask content
- Creates diverse subject matter (Physics, Math, Chemistry, etc.)
- Generates progress data for multiple users
- Supports command-line customization

**Usage:**
```bash
# Generate default data (10 lessons, 3 parts each, 4 exercises each, 2 subtasks each, 5 users)
python3 scripts/generate_fake_personalized_data.py

# Customize the generation
python3 scripts/generate_fake_personalized_data.py --count 5 --parts 4 --exercises 6 --subtasks 3 --users 3

# Save data to JSON files
python3 scripts/generate_fake_personalized_data.py --save

# Save to custom directory
python3 scripts/generate_fake_personalized_data.py --save --output my_test_data
```

**Command Line Options:**
- `--count N`: Number of lessons to generate (default: 10)
- `--parts N`: Number of parts per lesson (default: 3)
- `--exercises N`: Number of exercises per part (default: 4)
- `--subtasks N`: Number of subtasks per exercise (default: 2)
- `--users N`: Number of users for progress tracking (default: 5)
- `--output DIR`: Output directory for JSON files (default: fake_data)
- `--save`: Save generated data to JSON files

### 2. Simple Generator (`simple_fake_data_generator.py`)

**Features:**
- Quick generation of basic test data
- No external dependencies
- Perfect for quick API testing
- Generates smaller, manageable datasets

**Usage:**
```bash
# Generate simple test data
python3 scripts/simple_fake_data_generator.py
```

**Output:**
- 2 lessons
- 3 parts per lesson
- 2 exercises per part
- 50% chance of subtasks per exercise
- 3 users with progress tracking
- 40% chance of lesson extensions

## Generated Data Structure

### Lessons
```json
{
  "session_id": "uuid",
  "user_id": "uuid",
  "topic_id": "uuid",
  "title": "Physics: Mechanics - Lesson 1",
  "focus_area": "Physics",
  "proficiency_level": "beginner",
  "is_completed": false,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Lesson Parts
```json
{
  "id": "uuid",
  "lesson_id": "uuid",
  "title": "Part 1: Introduction and Overview",
  "description": "This section introduces the fundamental concepts...",
  "part_order": 1,
  "is_completed": false,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Exercises
```json
{
  "id": "uuid",
  "lesson_part_id": "uuid",
  "exercise_type": "multiple_choice",
  "title": "Multiple Choice: Understanding",
  "content": "What is the primary function of force?",
  "instructions": "Select the best answer from the options provided.",
  "correct_answer": "The correct answer involves understanding...",
  "explanation": "This concept is fundamental to understanding...",
  "difficulty_level": "easy",
  "exercise_order": 1,
  "is_completed": false,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Subtasks
```json
{
  "id": "uuid",
  "exercise_id": "uuid",
  "title": "Additional Explanation",
  "content": "Additional explanation of force",
  "subtask_type": "explanation",
  "subtask_order": 1,
  "is_optional": true,
  "is_completed": false,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Progress Records
```json
{
  "id": "uuid",
  "lesson_part_id": "uuid",
  "user_id": "uuid",
  "status": "in_progress",
  "progress_percentage": 75,
  "time_spent_minutes": 45,
  "started_at": "2024-01-01T00:00:00Z",
  "completed_at": null,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Lesson Extensions
```json
{
  "id": "uuid",
  "lesson_id": "uuid",
  "user_id": "uuid",
  "extension_type": "exercise",
  "parent_id": "uuid",
  "extension_reason": "Student needs more practice with force concepts",
  "created_at": "2024-01-01T00:00:00Z"
}
```

## Content Templates

### Exercise Types
- **multiple_choice**: Questions with predefined answer options
- **true_false**: True/false statements to verify
- **calculation**: Mathematical problem solving
- **explanation**: Conceptual understanding questions
- **interactive**: Hands-on activities and simulations

### Subtask Types
- **explanation**: Additional clarifications and details
- **practice**: Extra practice problems and exercises
- **reinforcement**: Review materials and summaries
- **extension**: Advanced topics and related concepts

### Difficulty Levels
- **easy**: Basic concepts and simple applications
- **medium**: Intermediate complexity and analysis
- **hard**: Advanced topics and complex problem solving

## Using Generated Data for API Testing

### 1. Generate Test Data
```bash
python3 scripts/simple_fake_data_generator.py
```

### 2. Check the Summary File
The `fake_data/summary.json` file contains:
- Count of each data type
- User IDs for testing
- Lesson IDs for testing
- Generation timestamp

### 3. Test API Endpoints

#### Create a Lesson Part
```bash
curl -X POST "http://localhost:8000/lesson-parts/" \
  -H "Content-Type: application/json" \
  -d @fake_data/lesson_parts.json
```

#### Create Exercises
```bash
curl -X POST "http://localhost:8000/personalized-exercises/" \
  -H "Content-Type: application/json" \
  -d @fake_data/exercises.json
```

#### Track Progress
```bash
curl -X POST "http://localhost:8000/personalized-progress/lesson-part" \
  -H "Content-Type: application/json" \
  -d '{
    "lesson_part_id": "uuid-from-summary",
    "user_id": "uuid-from-summary",
    "status": "in_progress",
    "progress_percentage": 50,
    "time_spent_minutes": 30
  }'
```

### 4. Test Data Relationships

The generated data maintains proper relationships:
- Each lesson part belongs to a lesson
- Each exercise belongs to a lesson part
- Each subtask belongs to an exercise
- Progress records reference the correct entities
- Extensions reference the correct lessons

## Customization Options

### Content Variety
The comprehensive generator includes:
- **10 subjects**: Physics, Math, Chemistry, Biology, Computer Science, etc.
- **Multiple topics per subject**: Mechanics, Algebra, Atomic Structure, etc.
- **Varied exercise content**: Different question types and difficulty levels
- **Realistic descriptions**: Educational content that makes sense

### Data Volume
- **Small datasets**: 2-5 lessons for quick testing
- **Medium datasets**: 10-20 lessons for comprehensive testing
- **Large datasets**: 50+ lessons for performance testing

### User Scenarios
- **Single user**: Test individual learning paths
- **Multiple users**: Test multi-user scenarios
- **Progress tracking**: Test completion and time tracking
- **Extensions**: Test adaptive learning features

## Best Practices

### 1. Start Small
- Begin with the simple generator for basic testing
- Use small datasets (2-5 lessons) for initial API testing
- Gradually increase complexity as needed

### 2. Validate Relationships
- Ensure all foreign keys reference valid entities
- Check that order values are sequential
- Verify that completion dates make sense

### 3. Test Edge Cases
- Test with empty datasets
- Test with maximum values
- Test with invalid relationships
- Test with missing optional fields

### 4. Monitor Performance
- Use large datasets to test API performance
- Monitor database query performance
- Test concurrent user scenarios

## Troubleshooting

### Common Issues

#### Import Errors
```bash
# Make sure you're in the project root directory
cd /path/to/tegus
python3 scripts/generate_fake_personalized_data.py
```

#### Database Connection Issues
- The generators work without database connections
- Use `--save` flag to export to JSON files
- Import JSON data manually for testing

#### Memory Issues with Large Datasets
- Reduce the number of entities generated
- Use the simple generator for large-scale testing
- Generate data in smaller batches

### Getting Help

1. **Check the generated summary file** for data counts and IDs
2. **Verify file permissions** for the output directory
3. **Use smaller datasets** if experiencing performance issues
4. **Check the console output** for error messages

## Examples

### Quick API Testing
```bash
# Generate minimal test data
python3 scripts/simple_fake_data_generator.py

# Test lesson parts endpoint
curl -X GET "http://localhost:8000/lesson-parts/lesson/$(jq -r '.lesson_ids[0]' fake_data/summary.json)"
```

### Comprehensive Testing
```bash
# Generate comprehensive test data
python3 scripts/generate_fake_personalized_data.py --count 20 --parts 5 --exercises 8 --subtasks 4 --users 10 --save

# Test all endpoints with realistic data
# Use the generated JSON files for bulk testing
```

### Custom Scenarios
```bash
# Generate physics-focused lessons
python3 scripts/generate_fake_personalized_data.py --count 5 --save

# Generate math exercises with many subtasks
python3 scripts/generate_fake_personalized_data.py --count 3 --subtasks 5 --save

# Generate data for performance testing
python3 scripts/generate_fake_personalized_data.py --count 100 --parts 10 --exercises 20 --users 50 --save
```

## Conclusion

These fake data generators provide a solid foundation for testing the personalized learning API. They create realistic, varied data that maintains proper relationships and covers all the different content types and scenarios your system needs to handle.

Start with the simple generator for basic testing, then use the comprehensive generator for more thorough testing scenarios. The generated data will help you verify that your API endpoints work correctly with various data combinations and edge cases.
