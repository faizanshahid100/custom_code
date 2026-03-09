# QUICK REFERENCE GUIDE

## What's New in Version 2.0?

### 🎯 Main Enhancement
**The module now automatically updates attendance and KPI records for the last 30 days!**

This means:
- ✅ Add attendance for March 1st on March 9th → March 1st record automatically updates
- ✅ Add KPI data for last week → All affected records automatically update  
- ✅ Daily job catches any retroactive entries you missed
- ✅ Manual update button for on-demand refresh

---

## How It Works Now

### Scenario 1: User Adds Past Attendance
```
You: Add attendance for 5 days ago
     ↓
System: Instantly finds the attendance KPI record for that date
     ↓
System: Updates attendance type from "Absent" to "Present"
     ↓
You: See updated record immediately
```

### Scenario 2: User Adds Past KPI Data
```
You: Enter daily progress for last week
     ↓
System: Finds employee from user
     ↓
System: Updates attendance KPI record with new KPI data
     ↓
System: Recalculates KPI percentage
     ↓
You: See updated performance metrics
```

### Scenario 3: Daily Scheduled Job (Automatic)
```
1:00 AM Every Day:
     ↓
System: Creates today's records
     ↓
System: Scans last 30 days for all employees
     ↓
System: Updates all records with latest data
     ↓
Next Morning: All your retroactive entries are processed
```

---

## Quick Actions

### For Regular Users

**Add Past Attendance:**
```
1. Go to Attendance module
2. Create attendance for any date
3. Done! The system updates automatically
```

**Add Past KPI Data:**
```
1. Go to Daily Progress
2. Enter KPI data for any date
3. Done! The system updates automatically
```

**View Updated Records:**
```
1. Go to: Attendance & KPI → Daily Records
2. Filter by date or employee
3. See all updates reflected
```

### For Administrators

**Force Update (Manual):**
```
1. Go to: Attendance & KPI → Update Last 30 Days
2. Click the menu item
3. Wait 30-60 seconds
4. Check logs for confirmation
```

**Check Scheduled Job:**
```
1. Settings → Technical → Scheduled Actions
2. Find: "Create Daily Attendance & KPI Records"
3. View execution logs
4. Verify next run time
```

**View Logs:**
```
Settings → Technical → Logging
Filter: employee.attendance.kpi
Look for: INFO, ERROR messages
```

---

## File Changes Summary

### New Files (3)
1. **models/hr_attendance.py**
   - Triggers when attendance is added/modified/deleted
   - Updates attendance KPI records automatically

2. **models/daily_progress.py**
   - Triggers when KPI data is added/modified/deleted
   - Refreshes KPI data in attendance records

3. **Documentation**
   - README.md - Full documentation
   - CHANGELOG.md - Version history
   - INSTALLATION.md - Setup guide
   - QUICK_REFERENCE.md - This file

### Modified Files (4)
1. **models/employee_attendance_kpi.py**
   - Added: `update_last_n_days_records()` method
   - Enhanced: `cron_create_daily_records()` method

2. **models/__init__.py**
   - Added imports for new models

3. **data/scheduled_action.xml**
   - Added server action for manual update
   - Added menu item "Update Last 30 Days"

4. **__manifest__.py**
   - Updated to version 2.0.0
   - Enhanced description

---

## Common Use Cases

### Use Case 1: Bulk Import Historical Data
```
Problem: Need to import 2 weeks of attendance data
Solution:
  1. Import all attendance records normally
  2. Go to: Attendance & KPI → Update Last 30 Days
  3. Wait for completion
  4. All records will be created/updated
```

### Use Case 2: Fix Incorrect Attendance
```
Problem: Employee was marked absent but was actually present
Solution:
  1. Add/modify attendance record for that date
  2. System automatically updates attendance KPI
  3. Record changes from "Absent" to "Present"
  4. No manual intervention needed
```

### Use Case 3: Late KPI Entry
```
Problem: Employee forgets to enter KPI data for last week
Solution:
  1. Employee enters daily progress for past dates
  2. System automatically updates all affected KPI records
  3. KPI percentages recalculated
  4. Reports show updated data
```

### Use Case 4: Monthly Review
```
Problem: Need to verify all data is current
Solution:
  1. Go to: Attendance & KPI → Update Last 30 Days
  2. Click to run manual update
  3. System processes all records
  4. Check logs for any errors
  5. Review reports with confidence
```

---

## Key Benefits

### For Employees
- ✅ Can add past data without worrying about records
- ✅ See accurate performance metrics
- ✅ No manual intervention needed

### For HR/Managers
- ✅ Always see up-to-date attendance data
- ✅ Accurate KPI performance tracking
- ✅ Reliable reports and analytics
- ✅ No missing data from retroactive entries

### For Administrators
- ✅ Automated data integrity
- ✅ Manual control when needed
- ✅ Comprehensive logging
- ✅ Error handling built-in

---

## Troubleshooting (Quick Fixes)

### Records not updating?
```
Fix: Go to Attendance & KPI → Update Last 30 Days
Expected: Updates all records in 30-60 seconds
```

### Can't find "Update Last 30 Days" menu?
```
Fix 1: Clear browser cache (Ctrl + Shift + Delete)
Fix 2: Reload page (Ctrl + F5)
Fix 3: Check user access rights
```

### Scheduled job not running?
```
Check: Settings → Technical → Scheduled Actions
Find: "Create Daily Attendance & KPI Records"
Verify: Active checkbox is checked
```

### KPI data not showing?
```
Check 1: Does daily.progress record exist for that date?
Check 2: Is employee linked to user?
Check 3: Run manual update
```

---

## Performance Notes

### Expected Times
- Single record update: < 1 second
- Manual 30-day update (100 employees): 30-60 seconds
- Daily scheduled job: Runs at 1:00 AM (off-hours)

### Optimization Tips
- Let scheduled job handle routine updates
- Use manual update for bulk imports
- Don't run manual update during peak hours
- Monitor logs for any errors

---

## Upgrade Checklist

Before upgrading:
- [ ] Backup database
- [ ] Note current record counts
- [ ] Stop scheduled actions (optional)

During upgrade:
- [ ] Replace module files
- [ ] Upgrade module
- [ ] Verify scheduled action is active

After upgrade:
- [ ] Run "Update Last 30 Days" once
- [ ] Test by adding past attendance
- [ ] Test by adding past KPI data
- [ ] Monitor logs for 24 hours

---

## Support

### Documentation
- Full docs: README.md
- Installation: INSTALLATION.md
- Changes: CHANGELOG.md

### Getting Help
1. Check logs first
2. Review this guide
3. Try manual update
4. Check documentation
5. Contact support with logs

---

## Version Info

**Current Version**: 2.0.0
**Odoo Version**: 16.0+
**Author**: Farooq Butt | Prime System Solutions
**Last Updated**: March 2025

---

## Quick Command Reference

### Python Console Commands
```python
# Manual update last 30 days
env['employee.attendance.kpi'].update_last_n_days_records(days=30)

# Run daily job manually
env['employee.attendance.kpi'].cron_create_daily_records()

# Count records
env['employee.attendance.kpi'].search_count([])

# Find today's records
env['employee.attendance.kpi'].search([('date', '=', fields.Date.today())])
```

### SQL Queries (PostgreSQL)
```sql
-- Count records by date
SELECT date, COUNT(*) FROM employee_attendance_kpi GROUP BY date ORDER BY date DESC;

-- Check recent updates
SELECT * FROM employee_attendance_kpi WHERE write_date > NOW() - INTERVAL '1 hour';

-- Find records by attendance type
SELECT attendance_type, COUNT(*) FROM employee_attendance_kpi GROUP BY attendance_type;
```

---

## Tips & Tricks

### Tip 1: Batch Processing
For large bulk imports, import in batches and run manual update after each batch.

### Tip 2: Data Validation
After significant changes, always run manual update to ensure consistency.

### Tip 3: Monitoring
Set up a daily check of logs to catch any processing errors early.

### Tip 4: Performance
If system is slow, reduce update period from 30 to 15 days temporarily.

### Tip 5: Testing
Always test retroactive updates in development environment first.

---

**Remember**: The system now handles retroactive data automatically. Just add your data whenever you need to, and the system will ensure everything is up-to-date! ✅
