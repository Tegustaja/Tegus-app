# Frontend Calibration Implementation

## Overview

The frontend now includes a complete calibration system that prevents users from accessing subjects until they complete an initial assessment. All text is in Estonian as requested.

## Components Added

### 1. Calibration Context (`context/calibration-provider.tsx`)
- Tracks calibration status: `not_started`, `in_progress`, `completed`
- Automatically checks if user has completed diagnostics
- Provides methods to start and complete calibration

### 2. Calibration Screen (`app/(app)/(protected)/calibration.tsx`)
- Full-screen calibration assessment
- Shows questions from different subjects
- Collects confidence ratings and response times
- Estonian language interface

### 3. Updated Home Subjects Grid (`_HomeSubjectsGrid.tsx`)
- Shows calibration button when needed
- Disables subjects until calibration complete
- Estonian text for calibration prompt

### 4. Updated Main Home Screen (`index.tsx`)
- Integrates with calibration context
- Shows loading state while checking calibration
- Conditionally enables/disables subjects

## How It Works

### 1. User Registration/Login
- System automatically checks if user has completed calibration
- Queries `diagnostic_events` table for existing data

### 2. First Visit (No Calibration)
- All subjects appear faded and disabled
- Large calibration button appears below subjects
- Button text: "Alusta kalibreerimist" (Start Calibration)
- Subtitle: "Enne õppimise alustamist peame mõistma sinu praegust taset" (Before starting to learn, we need to understand your current level)

### 3. Calibration Process
- User clicks calibration button
- Redirected to `/calibration` screen
- Shows welcome message in Estonian
- Presents questions from different subjects
- Each question includes confidence rating (1-5 scale)
- Progress bar shows completion status

### 4. After Calibration
- User redirected back to dashboard
- All subjects now enabled and clickable
- Calibration button disappears
- User can start learning normally

## Estonian Text Used

### Dashboard
- **Calibration Button**: "Alusta kalibreerimist"
- **Subtitle**: "Enne õppimise alustamist peame mõistma sinu praegust taset"
- **Loading**: "Laadimine..."

### Calibration Screen
- **Welcome**: "Tere tulemast Tegus'i!"
- **Description**: "Enne õppimise alustamist peame mõistma sinu praegust taset. See võtab ainult mõne minuti ja aitab meil pakkuda sulle parimat õppekogemust."
- **Question Header**: "Kalibreerimisküsimus X / Y"
- **Question Subtitle**: "See aitab meil mõista sinu praegust taset"
- **Confidence Question**: "Kui kindel sa oled oma vastuses?"
- **Progress**: "Edenemine"
- **Instructions**: "💡 Vasta küsimustele nii hästi kui suudad. Kui sa ei tea vastust, vali madal usaldustase."
- **Completion Alert**: "Kalibreerimine lõpetatud! Nüüd saad alustada õppimist. Sinu tulemused aitavad meil pakkuda sulle sobivat sisu."

## Technical Implementation

### Context Integration
```typescript
// In main layout
<AuthProvider>
  <CalibrationProvider>
    <Stack>
      {/* Routes */}
    </Stack>
  </CalibrationProvider>
</AuthProvider>
```

### Status Checking
```typescript
const { calibrationStatus, isLoading } = useCalibration();

const needsCalibration = calibrationStatus === 'not_started';
const canStartLearning = calibrationStatus === 'completed';
```

### Subject Disabling
```typescript
subjects={availableSubjects.map(s => ({ 
  ...s, 
  is_unlocked: canStartLearning 
}))}
```

### Calibration Button
```typescript
<HomeSubjectsGrid 
  subjects={subjects}
  isDesktop={isDesktop}
  showCalibrationButton={needsCalibration}
  onCalibrationPress={() => router.push('/calibration')}
/>
```

## Database Requirements

The system requires these tables to be created:
- `student_topic_state` - for tracking learning metrics
- `diagnostic_events` - for storing calibration responses

## Testing the Implementation

1. **Fresh User**: Should see disabled subjects and calibration button
2. **Calibration Flow**: Click button → complete questions → return to enabled subjects
3. **Returning User**: Should see enabled subjects immediately

## Future Enhancements

- **Subject-Specific Calibration**: Different questions per subject
- **Adaptive Question Selection**: Choose questions based on user responses
- **Calibration History**: Allow users to retake calibration
- **Progress Tracking**: Show calibration completion percentage
- **Skip Option**: Allow users to skip calibration (with warning)

## Troubleshooting

### Common Issues
1. **Subjects Not Disabling**: Check calibration context integration
2. **Calibration Button Not Showing**: Verify `needsCalibration` logic
3. **Navigation Errors**: Ensure calibration route is added to layout
4. **Context Errors**: Verify provider hierarchy in main layout

### Debug Steps
1. Check browser console for errors
2. Verify calibration context values
3. Check database tables exist
4. Verify API endpoints are working

