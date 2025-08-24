# Topic Locking System

This document explains how the topic locking system works in Tegus, which ensures students complete topics in the correct order for optimal learning progression.

## Overview

The topic locking system prevents students from jumping ahead to advanced topics before mastering the prerequisites. Topics are unlocked sequentially as the user completes each one.

## How It Works

### 1. **Sequential Unlocking**
- **First topic**: Always unlocked
- **Subsequent topics**: Unlocked only when all previous topics are completed
- **Locked topics**: Cannot be accessed until prerequisites are met

### 2. **Database Structure**

The system uses the `user_topic_completion` table to track:
- `user_id`: References the Supabase Auth user
- `topic_id`: The topic being tracked
- `is_completed`: Boolean indicating completion
- `progress_percentage`: Progress from 0-100%
- `mastery_level`: Skill level from 0.0-1.0
- `completed_at`: When the topic was completed
- `last_accessed`: Last interaction timestamp

### 3. **Locking Logic**

```typescript
function shouldTopicBeLocked(
  topicIndex: number, 
  completedTopicIds: string[], 
  allTopics: Topic[]
): boolean {
  // First topic is always unlocked
  if (topicIndex === 0) {
    return false;
  }
  
  // Check if all previous topics are completed
  for (let i = 0; i < topicIndex; i++) {
    const previousTopic = allTopics[i];
    if (!completedTopicIds.includes(previousTopic.id)) {
      return true; // Lock if any previous topic is not completed
    }
  }
  
  return false; // Unlock if all previous topics are completed
}
```

### 4. **Visual Indicators**

Topics display different states:
- 🔒 **Locked**: Gray circle with lock icon
- 🔓 **Available**: Blue circle with topic icon
- 📚 **Started**: Blue circle with progress indicator
- ✅ **Completed**: Green circle with checkmark

## API Functions

### Core Functions

#### `getUserCompletedTopics(userId, subjectId)`
Returns array of completed topic IDs for a user in a subject.

#### `shouldTopicBeLocked(topicIndex, completedTopicIds, allTopics)`
Determines if a topic should be locked based on completion status.

#### `markTopicAsCompleted(userId, topicId, masteryLevel)`
Marks a topic as completed when a lesson is finished.

#### `updateTopicProgress(userId, topicId, progressPercentage, masteryLevel)`
Updates progress for a topic (auto-completes at 100%).

### Usage Examples

```typescript
// Check completion status
const completedTopics = await getUserCompletedTopics(userId, 'physics');

// Update progress
await updateTopicProgress(userId, topicId, 75, 0.8);

// Mark as completed
await markTopicAsCompleted(userId, topicId, 0.9);
```

## Frontend Integration

### Topics Page (`/topics`)

The topics page automatically:
1. Fetches user's completed topics
2. Applies locking logic to each topic
3. Displays appropriate visual states
4. Prevents interaction with locked topics

### Visual States

```typescript
interface TopicWithProgress {
  progress: number;          // 0-100%
  isLocked: boolean;         // Calculated locking status
  hasStarted: boolean;       // Has any progress
  isCompleted: boolean;      // 100% complete
}
```

### Topic Card Rendering

```typescript
// Circle color based on status
const circleColor = topic.isLocked 
  ? 'bg-gray-400'           // Locked
  : topic.isCompleted
    ? 'bg-green-500'        // Completed
    : topic.hasStarted 
      ? 'bg-blue-500'       // In progress
      : 'bg-blue-400';      // Available

// Icon based on status
const icon = topic.isLocked 
  ? <Lock />                // Lock icon
  : topic.isCompleted 
    ? <Check />             // Checkmark
    : <TopicIcon />;        // Topic-specific icon
```

## Testing the System

### Manual Testing

1. **Install dependencies** and set up environment
2. **Run the test script**:
   ```bash
   python3 test_topic_completion.py
   ```
3. **Open the topics page** in your app
4. **Observe locking behavior**

### Test Scenarios

1. **New User**: Only first topic unlocked
2. **Partial Progress**: Some topics completed, next one unlocked
3. **Advanced User**: Multiple topics completed, advanced ones unlocked

## Implementation Details

### Database Migration

The system was implemented by:
1. Removing the old `profiles` table
2. Adding `user_topic_completion` table
3. Updating all user references to use Supabase Auth
4. Adding completion tracking triggers

### Performance Considerations

- **Efficient queries**: Single query to get all completions
- **Client-side logic**: Locking calculation done in frontend
- **Caching**: Completion status cached per session

### Security

- **Row Level Security**: Users can only see their own completion data
- **Server validation**: Backend validates completion requests
- **Auth integration**: Uses Supabase Auth for user identification

## Benefits

1. **Learning Progression**: Ensures proper skill building
2. **User Guidance**: Clear path through curriculum
3. **Motivation**: Achievement system with unlocks
4. **Data Insights**: Track user progression patterns

## Future Enhancements

### Planned Features

1. **Flexible Prerequisites**: Custom prerequisite rules
2. **Skill Trees**: Branching learning paths
3. **Adaptive Unlocking**: AI-based progression decisions
4. **Achievement Badges**: Completion rewards
5. **Progress Analytics**: Detailed learning insights

### Configuration Options

```typescript
interface LockingConfig {
  strictMode: boolean;        // Require 100% completion
  masteryThreshold: number;   // Minimum mastery level (0.0-1.0)
  allowSkipping: boolean;     // Admin override capability
  adaptiveUnlocking: boolean; // AI-based decisions
}
```

## Troubleshooting

### Common Issues

1. **Topics not unlocking**: Check completion status in database
2. **Visual glitches**: Clear app cache and reload
3. **Performance issues**: Optimize completion queries

### Debug Tools

```typescript
// Log completion status
console.log('Completed topics:', completedTopicIds);

// Log locking decisions
console.log('Topics with locking:', topics.map(t => ({
  name: t.name,
  isLocked: t.isLocked,
  reason: getLockingReason(t)
})));
```

## Conclusion

The topic locking system provides a structured learning experience that guides students through the curriculum in the optimal order. By preventing users from skipping ahead, it ensures solid foundation building and improves learning outcomes.

The system is flexible, performant, and provides clear visual feedback to users about their progress and next steps.
