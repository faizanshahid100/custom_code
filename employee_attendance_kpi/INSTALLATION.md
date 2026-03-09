# Installation & Upgrade Guide

## New Installation (Version 2.0)

### Prerequisites
- Odoo 16.0 or higher
- Modules: `hr`, `base`, `prime_sol_custom`
- PostgreSQL database

### Installation Steps

1. **Copy Module**
   ```bash
   cp -r employee_attendance_kpi /path/to/odoo/addons/
   ```

2. **Restart Odoo Server**
   ```bash
   sudo systemctl restart odoo
   # OR
   ./odoo-bin -c /path/to/odoo.conf --stop-after-init
   ./odoo-bin -c /path/to/odoo.conf
   ```

3. **Update Apps List**
   - Go to Apps menu
   - Click "Update Apps List"
   - Search for "Employee Attendance & KPI Tracking"

4. **Install Module**
   - Click "Install"
   - Wait for installation to complete

5. **Verify Installation**
   - Check menu: Attendance & KPI → Daily Records
   - Check menu: Attendance & KPI → Update Last 30 Days
   - Go to Settings → Technical → Scheduled Actions
   - Find "Create Daily Attendance & KPI Records" (should be active)

6. **Initial Data Population**
   - Option A (Automatic): Wait for scheduled job at 1:00 AM
   - Option B (Manual): Go to Attendance & KPI → Update Last 30 Days and click

---

## Upgrade from Version 1.0 to 2.0

### Pre-Upgrade Checklist
- [x] Backup your database
- [x] Note current record counts
- [x] Export critical data if needed
- [x] Stop scheduled actions temporarily (optional)

### Upgrade Steps

#### 1. Backup Database
```bash
# PostgreSQL backup
pg_dump -U odoo_user -d your_database > backup_before_upgrade.sql

# OR using Odoo interface
# Go to Settings → Database Manager → Backup
```

#### 2. Stop Odoo Server
```bash
sudo systemctl stop odoo
```

#### 3. Replace Module Files
```bash
# Backup old version
mv /path/to/odoo/addons/employee_attendance_kpi /path/to/backup/employee_attendance_kpi_v1

# Copy new version
cp -r employee_attendance_kpi /path/to/odoo/addons/
```

#### 4. Update File Permissions
```bash
chown -R odoo:odoo /path/to/odoo/addons/employee_attendance_kpi
chmod -R 755 /path/to/odoo/addons/employee_attendance_kpi
```

#### 5. Start Odoo Server
```bash
sudo systemctl start odoo
```

#### 6. Upgrade Module
**Method A: Through Odoo Interface**
1. Go to Apps menu
2. Remove "Apps" filter
3. Search for "Employee Attendance"
4. Click "Upgrade"
5. Wait for completion

**Method B: Command Line**
```bash
./odoo-bin -c /path/to/odoo.conf -u employee_attendance_kpi --stop-after-init
./odoo-bin -c /path/to/odoo.conf
```

#### 7. Post-Upgrade Verification

**Check Scheduled Action:**
```
Settings → Technical → Scheduled Actions
→ Find "Create Daily Attendance & KPI Records"
→ Verify it's active
→ Check "Next Execution Date"
```

**Check New Menu Items:**
```
Attendance & KPI → Update Last 30 Days
(This should be a new menu item)
```

**Check Models:**
```python
# In Odoo shell or Python code
self.env['employee.attendance.kpi'].search_count([])
# Should return count of existing records (unchanged)
```

#### 8. Initial 30-Day Update (Recommended)
1. Navigate to: Attendance & KPI → Update Last 30 Days
2. Click to execute
3. Wait for completion (may take 30-60 seconds)
4. Check logs: Settings → Technical → Logging

**Expected Log Output:**
```
INFO: Updating attendance KPI records for the last 30 days
INFO: Updated XXX records and created YYY new records for the last 30 days
```

#### 9. Test New Features

**Test A: Past Attendance Entry**
1. Go to Attendance
2. Add attendance for 5 days ago
3. Go to Attendance & KPI → Daily Records
4. Find the record for 5 days ago
5. Verify attendance_type changed to "Present"

**Test B: Past KPI Entry**
1. Go to Daily Progress
2. Add/modify data for 3 days ago
3. Go to Attendance & KPI → Daily Records
4. Find the record for 3 days ago
5. Verify KPI fields are updated

**Test C: Scheduled Job**
1. Wait until next scheduled run (1:00 AM)
2. Next morning, check logs
3. Verify both daily creation and 30-day update executed

---

## Troubleshooting

### Issue: Upgrade Fails

**Symptoms:**
- Error message during upgrade
- Module shows "To Upgrade" but won't upgrade

**Solutions:**
```bash
# Check Odoo logs
tail -f /var/log/odoo/odoo-server.log

# Try upgrading with full logs
./odoo-bin -c /path/to/odoo.conf -u employee_attendance_kpi -d your_database --log-level=debug

# Check for module dependencies
# Ensure prime_sol_custom is installed and up to date
```

### Issue: Scheduled Action Not Running

**Symptoms:**
- Daily job doesn't execute
- Records not being created/updated

**Solutions:**
1. Check if scheduled action is active:
   ```
   Settings → Technical → Scheduled Actions
   → Find "Create Daily Attendance & KPI Records"
   → Ensure "Active" is checked
   ```

2. Manually trigger:
   ```python
   # In Odoo shell
   env['employee.attendance.kpi'].cron_create_daily_records()
   ```

3. Check server logs for errors

### Issue: Records Not Updating on Data Entry

**Symptoms:**
- Adding past attendance doesn't update KPI records
- Adding past KPI data doesn't reflect

**Solutions:**
1. Verify new models are loaded:
   ```python
   # Check if models exist
   env['hr.attendance']._inherit
   env['daily.progress']._inherit
   # Should show 'hr.attendance' and 'daily.progress'
   ```

2. Restart Odoo server completely:
   ```bash
   sudo systemctl restart odoo
   ```

3. Check for Python errors in logs

### Issue: "Update Last 30 Days" Menu Missing

**Symptoms:**
- Can't find manual update menu
- Menu item doesn't appear

**Solutions:**
1. Clear browser cache
2. Reload page (Ctrl + F5)
3. Check if user has access rights
4. Verify server action exists:
   ```
   Settings → Technical → Server Actions
   → Search for "Update Last 30 Days"
   ```

### Issue: Performance is Slow

**Symptoms:**
- 30-day update takes too long
- System becomes unresponsive

**Solutions:**
1. Reduce update period temporarily:
   ```python
   # Instead of 30 days, try 15
   env['employee.attendance.kpi'].update_last_n_days_records(days=15)
   ```

2. Run updates during off-hours
3. Optimize database:
   ```sql
   VACUUM ANALYZE employee_attendance_kpi;
   ```

4. Add database indexes if needed

---

## Rollback Instructions

If you need to rollback to version 1.0:

### 1. Restore Database Backup
```bash
# Stop Odoo
sudo systemctl stop odoo

# Restore database
psql -U odoo_user -d your_database < backup_before_upgrade.sql
```

### 2. Replace Module Files
```bash
# Remove v2.0
rm -rf /path/to/odoo/addons/employee_attendance_kpi

# Restore v1.0
cp -r /path/to/backup/employee_attendance_kpi_v1 /path/to/odoo/addons/employee_attendance_kpi
```

### 3. Restart Odoo
```bash
sudo systemctl start odoo
```

### 4. Verify
- Check that module shows correct version
- Test basic functionality
- Verify scheduled action works

---

## Post-Installation Configuration

### Adjust Update Period

To change from 30 days to a different period:

**Method 1: Code Modification**
```python
# In models/employee_attendance_kpi.py, line ~285
# Change:
self.update_last_n_days_records(days=30)
# To:
self.update_last_n_days_records(days=60)  # For 60 days
```

**Method 2: Custom Server Action**
```
Settings → Technical → Server Actions → Create
Name: Update Last 60 Days
Model: employee.attendance.kpi
Action To Do: Execute Python Code
Python Code:
    model.update_last_n_days_records(days=60)
```

### Customize Scheduled Job Time

```
Settings → Technical → Scheduled Actions
→ "Create Daily Attendance & KPI Records"
→ Modify "Next Execution Date"
→ Change hour/minute as needed
```

### Add Email Notifications

Can be configured through Automated Actions:
```
Settings → Technical → Automated Actions → Create
Model: employee.attendance.kpi
Trigger: On Creation
Action: Send Email (configure template)
```

---

## Data Migration (Optional)

If you have historical data to import:

### CSV Import Template
```csv
employee_id/id,date,ticket_resolved,CAST,billable_hours,avg_resolution_time
hr.employee_1,2024-01-01,10,5,8,2.5
hr.employee_1,2024-01-02,12,6,8,2.3
```

### Import Steps
1. Prepare CSV with above format
2. Go to Attendance & KPI → Daily Records
3. Click Import
4. Map fields
5. Import
6. After import, run "Update Last 30 Days" to ensure calculations are correct

---

## Monitoring and Maintenance

### Daily Monitoring
- Check scheduled action execution logs
- Verify record counts are increasing
- Monitor for error logs

### Weekly Maintenance
- Review and clear old logs
- Verify data accuracy with spot checks
- Check database size and performance

### Monthly Tasks
- Backup database
- Review and optimize slow queries
- Archive old records if needed (>1 year)

---

## Support Contacts

For technical support:
- **Developer**: Farooq Butt
- **Company**: Prime System Solutions
- **Website**: https://www.primesystemsolutions.com

For issues:
1. Check logs first
2. Review this guide
3. Test in development environment
4. Contact support with full error logs
