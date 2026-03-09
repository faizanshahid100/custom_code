# Employee Attendance KPI Module - Enhanced Version

## Overview
This enhanced module automatically tracks employee attendance and KPI performance with **automatic 30-day retroactive updates** and **week/sprint number tracking**. Historical records are always accurate and up-to-date.

## Key Features

### 1. **Week/Sprint Number Tracking** (NEW in v2.1)
- Automatic week number calculation (Sprint_1, Sprint_2, etc.)
- Based on ISO 8601 standard (week starts Monday)
- Group by week/sprint in all views
- Perfect for Agile teams and sprint-based planning
- **Documentation**: See WEEK_NUMBER_FEATURE.md

### 2. **Automatic 30-Day Retroactive Updates**
The module now automatically handles retroactive data entry through multiple mechanisms:

#### Daily Scheduled Job Enhancement
- **Original**: Only created records for the current day
- **Enhanced**: Creates today's records AND updates the last 30 days of records
- **Schedule**: Runs daily at 1:00 AM
- **Location**: `data/scheduled_action.xml`

#### Real-Time Updates on Data Entry
The module now includes triggers that automatically update attendance KPI records when:

**A. Attendance Data Changes** (`models/hr_attendance.py`)
- When attendance is **created** for any date
- When attendance is **modified** 
- When attendance is **deleted**
- Automatically updates the corresponding attendance KPI record

**B. KPI Data Changes** (`models/daily_progress.py`)
- When daily progress (KPI data) is **created** for any date
- When KPI fields are **modified** (ticket_resolved, CAST, billable_hours, avg_resolution_time)
- When daily progress is **deleted**
- Automatically fetches and updates KPI data in attendance records

### 2. **Manual Update Option**
Added a manual update feature for administrators:

- **Menu Location**: Attendance & KPI → Update Last 30 Days
- **Function**: Manually trigger a full update of the last 30 days
- **Use Case**: If you notice discrepancies or after bulk data imports
- **Server Action**: `action_update_last_30_days`

### 3. **Smart Update Logic**

The update mechanism:
1. **Scans** the last 30 days for all active employees
2. **Updates** existing records:
   - Recomputes attendance type (Present/Absent/Leave/Weekend/Gazetted)
   - Fetches latest KPI data from daily.progress
   - Recalculates KPI percentages
3. **Creates** missing records for dates without entries
4. **Logs** all operations for audit trail

## How It Works

### Workflow Example 1: User Enters Past Attendance
```
Day 0: User adds attendance for March 1st (7 days ago)
       ↓
       System automatically updates March 1st attendance KPI record
       ↓
       Attendance type changes from "Absent" to "Present"
       ↓
       KPI percentages recalculated if KPI data exists
```

### Workflow Example 2: User Enters Past KPI Data
```
Day 0: User enters daily.progress data for March 5th
       ↓
       System finds employee linked to the user
       ↓
       Searches for March 5th attendance KPI record
       ↓
       Updates KPI fields (tickets, calls, hours, response time)
       ↓
       Recalculates KPI percentage based on employee targets
```

### Workflow Example 3: Daily Scheduled Job
```
1:00 AM Daily:
       ↓
       Creates records for today (if not exist)
       ↓
       Scans last 30 days for all active employees
       ↓
       Updates all records with latest data
       ↓
       Ensures all retroactive entries are captured
```

## File Structure

### New Files
```
models/
  ├── hr_attendance.py         # Triggers on attendance changes
  └── daily_progress.py        # Triggers on KPI data changes
```

### Modified Files
```
models/
  ├── __init__.py              # Added new model imports
  └── employee_attendance_kpi.py  # Added update_last_n_days_records() method
                                   # Enhanced cron_create_daily_records()

data/
  └── scheduled_action.xml     # Added manual update server action
```

## Technical Details

### New Methods

#### `update_last_n_days_records(days=30)`
- **Purpose**: Update attendance and KPI records for the last N days
- **Parameters**: 
  - `days` (int): Number of days to look back (default: 30)
- **Returns**: True on completion
- **Usage**: Can be called manually or by scheduled job

#### Enhanced `cron_create_daily_records()`
- **Purpose**: Daily scheduled job
- **Actions**: 
  1. Creates today's records
  2. Updates last 30 days
- **Returns**: True on completion

### Trigger Mechanisms

#### HR Attendance Triggers
```python
# On Create
def create(self, vals_list):
    # Creates attendance record
    # Triggers update of attendance KPI record

# On Write  
def write(self, vals):
    # Updates attendance record
    # Triggers update of attendance KPI record

# On Delete
def unlink(self):
    # Deletes attendance record
    # Triggers update of attendance KPI record (marks as absent)
```

#### Daily Progress Triggers
```python
# On Create
def create(self, vals_list):
    # Creates daily progress record
    # Triggers KPI data fetch for attendance record

# On Write (KPI fields only)
def write(self, vals):
    # Updates KPI fields
    # Triggers KPI data refresh for attendance record

# On Delete
def unlink(self):
    # Deletes daily progress record
    # Triggers KPI data reset for attendance record
```

## Performance Considerations

### Optimizations
- **Targeted Updates**: Only updates affected records, not all records
- **Batch Processing**: Daily job processes in batches
- **Error Handling**: Continues processing even if individual records fail
- **Logging**: Comprehensive logging for monitoring and debugging

### Expected Performance
- **Single Record Update**: < 1 second
- **30-Day Update (100 employees)**: ~30-60 seconds
- **Daily Scheduled Job**: Runs during off-hours (1:00 AM)

## Usage Instructions

### For End Users
1. **Add Past Attendance**: 
   - Go to Attendance module
   - Add attendance for any past date
   - System automatically updates the attendance KPI record

2. **Add Past KPI Data**:
   - Go to Daily Progress
   - Enter KPI data for any past date
   - System automatically updates the attendance KPI record

3. **View Updated Records**:
   - Navigate to Attendance & KPI → Daily Records
   - Filter by date range to see updated records
   - All retroactive changes will be reflected

### For Administrators
1. **Manual Update**:
   - Navigate to Attendance & KPI → Update Last 30 Days
   - Click to trigger immediate update
   - Check logs for completion status

2. **Monitor Scheduled Job**:
   - Go to Settings → Technical → Scheduled Actions
   - Find "Create Daily Attendance & KPI Records"
   - Check execution logs

3. **Adjust Update Period**:
   - Can modify the 30-day period by calling:
   ```python
   self.env['employee.attendance.kpi'].update_last_n_days_records(days=60)
   ```

## Logging

All operations are logged with:
- **INFO**: Successful operations
- **DEBUG**: Detailed processing information  
- **ERROR**: Failed operations with stack traces
- **WARNING**: Missing data or unusual conditions

Check logs at: Settings → Technical → Logging

## Upgrade Instructions

1. **Backup** your database
2. **Update** the module code
3. **Upgrade** the module from Apps menu
4. **Run** manual update for last 30 days (optional but recommended)
5. **Verify** records are updating correctly

## Troubleshooting

### Issue: Records Not Updating
**Solution**: 
- Check if scheduled action is active
- Run manual update
- Check logs for errors

### Issue: Missing KPI Data
**Solution**:
- Verify daily.progress records exist for the dates
- Check user-employee linking
- Ensure employee has user_id set

### Issue: Incorrect Attendance Type
**Solution**:
- Verify resource calendar is set for employee
- Check leave records and dates
- Review gazetted holiday configuration

## Support

For issues or questions:
1. Check the logs for error messages
2. Verify data in hr.attendance and daily.progress
3. Run manual update to force refresh
4. Review this README for configuration details

## Version History

### Version 2.0 (Current)
- Added automatic 30-day retroactive updates
- Real-time triggers on attendance changes
- Real-time triggers on KPI data changes
- Manual update option
- Enhanced logging and error handling

### Version 1.0 (Previous)
- Daily record creation
- Basic KPI tracking
- Attendance type computation
