# Weekly Records Feature - Complete Guide

## Overview
The **Weekly Records** feature automatically aggregates daily attendance and KPI data into weekly summaries. This provides a comprehensive view of employee performance by sprint/week, making it perfect for sprint planning, weekly reviews, and performance tracking.

## Key Features

### 📊 Automatic Weekly Aggregation
- **Attendance Summary**: Total working days, present, absent, leave days
- **KPI Totals**: Sum of all KPIs for the week
- **KPI Averages**: Average performance per working day
- **Attendance %**: Percentage of present days vs working days
- **Weekly KPI %**: Performance against weekly targets

### 🎯 Weekly Targets
Set weekly targets for:
- **Tickets Resolved**: Total tickets to resolve per week
- **Calls**: Total calls to handle per week
- **Billable Hours**: Total billable hours per week
- **Response Time**: Target average response time

### 📅 Automatic Generation
- Weekly records auto-generate from daily records
- Scheduled job runs daily at 2:00 AM
- Updates last 4 weeks automatically
- Manual refresh available

---

## How It Works

### Data Flow

```
Daily Records (7 days)
         ↓
    Aggregation
         ↓
Weekly Record Generated
         ↓
  - Attendance summary
  - KPI totals
  - KPI averages
  - Performance %
```

### Calculation Logic

#### Attendance Summary
```
Working Days = Total Days (7) - Weekend Days - Gazetted Holiday Days
Present Days = Count of "Present" attendance type
Absent Days = Count of "Absent" attendance type  
Leave Days = Count of "Leave" attendance type
Attendance % = (Present Days / Working Days) × 100
```

#### KPI Totals (Weekly Sum)
```
Total Tickets = Sum of all daily tickets for the week
Total Calls = Sum of all daily calls for the week
Total Billable Hours = Sum of all daily billable hours for the week
```

#### KPI Averages (Per Working Day)
```
Avg Tickets/Day = Total Tickets / Present Days
Avg Calls/Day = Total Calls / Present Days
Avg Billable Hours/Day = Total Billable Hours / Present Days
Avg Response Time = Average of daily response times (present days only)
```

#### Weekly KPI Performance
```
Same weighted calculation as daily records:
- Each assigned KPI gets equal weight
- Compare actual totals vs weekly targets
- Calculate weighted average percentage
```

---

## Setting Up Weekly Targets

### Step 1: Open Employee Record
1. Go to Employees
2. Open an employee record
3. Navigate to "KPI Targets" tab

### Step 2: Set Weekly Targets
```
Weekly Ticket Target: 50          (50 tickets per week)
Weekly Calls Target: 100          (100 calls per week)
Weekly Billable Hours Target: 40  (40 hours per week)
Weekly Response Time Target: 2.0  (2 hours average)
```

### Example Calculation
If employee sets:
- Weekly Ticket Target: 50
- Weekly Calls Target: 100

And achieves:
- Total Tickets: 45
- Total Calls: 110

**Weekly KPI %** = ((45/50 × 100) × 50%) + ((110/100 × 100) × 50%)
                 = (90% × 50%) + (100% × 50%)
                 = 45% + 50%
                 = **95%**

---

## Using Weekly Records

### View Weekly Records

**Menu**: Attendance & KPI → Weekly Records

**List View Shows**:
- Year and Week Number (Sprint_X)
- Week Start and End Dates
- Employee Name
- Working Days, Present Days, Absent Days
- Attendance %
- Total Tickets, Calls, Billable Hours
- Weekly KPI %

### Filter Options

**Predefined Filters**:
- **Current Week**: Shows only the current week
- **Current Year**: All weeks in current year
- **Last 4 Weeks**: Recent 4 weeks
- **Good Attendance (≥90%)**: High performers
- **Average Attendance (70-90%)**: Medium performers
- **Poor Attendance (<70%)**: Needs attention

**Group By**:
- Employee: See all weeks for each employee
- Year: Organize by year
- Week/Sprint: Group by sprint number

### Example View

```
Year | Week      | Week Start  | Week End    | Employee    | Working | Present | Absent | Attendance % | Total Tickets | Weekly KPI %
-----|-----------|-------------|-------------|-------------|---------|---------|--------|--------------|---------------|-------------
2024 | Sprint_10 | 2024-03-04  | 2024-03-10  | John Doe    | 5       | 5       | 0      | 100%         | 45            | 95%
2024 | Sprint_10 | 2024-03-04  | 2024-03-10  | Jane Smith  | 5       | 4       | 1      | 80%          | 38            | 85%
2024 | Sprint_11 | 2024-03-11  | 2024-03-17  | John Doe    | 5       | 5       | 0      | 100%         | 52            | 102%
```

---

## Weekly Record Details

### Form View Sections

#### 1. Basic Information
- Employee Name
- Year
- Week/Sprint Number
- Week Start Date
- Week End Date
- Total Days (usually 7)

#### 2. Attendance Summary Tab
**Days Breakdown**:
- Working Days: 5
- Present Days: 4
- Absent Days: 1
- Leave Days: 0

**Non-Working Days**:
- Weekend Days: 2
- Gazetted Holiday Days: 0
- Attendance %: 80%

#### 3. KPI Totals Tab
**Weekly Totals** (with targets):
- Total Tickets Resolved: 45 / Target: 50
- Total Calls: 110 / Target: 100
- Total Billable Hours: 38 / Target: 40
- Weekly KPI %: 95%

#### 4. Daily Averages Tab
**Average Per Day** (Present Days Only):
- Avg Tickets/Day: 11.25
- Avg Calls/Day: 27.5
- Avg Billable Hours/Day: 9.5
- Avg Response Time: 2.3 hours

---

## Scheduled Jobs

### Daily Record Generation
**Schedule**: Every day at 1:00 AM
**Function**: Creates/updates daily records

### Weekly Record Generation
**Schedule**: Every day at 2:00 AM
**Function**: 
1. Creates/updates current week record
2. Updates last 4 weeks
3. Ensures all weekly data is current

**Why Daily?**
- Catches retroactive daily entries
- Updates weekly totals when daily data changes
- Keeps weekly records fresh

---

## Manual Updates

### Refresh Weekly Data Button
Located in weekly record form view

**What It Does**:
1. Recomputes attendance summary
2. Recalculates KPI totals
3. Updates KPI averages
4. Refreshes weekly KPI %

**When to Use**:
- After bulk daily data import
- After correcting daily records
- If weekly data seems stale
- For verification/audit

### Update Last 4 Weeks
Available via scheduled action

**How to Run**:
```python
env['employee.attendance.kpi.weekly'].update_last_n_weeks_records(weeks=4)
```

**Use Cases**:
- After system maintenance
- After data corrections
- Before important reports
- Monthly reconciliation

---

## Reporting & Analytics

### Pivot Analysis

**Common Setups**:

**1. Employee Performance by Week**
```
Row: Employee
Row: Week Number
Column: Year
Measure: Weekly KPI %
```

**2. Attendance Trends**
```
Row: Week Number
Column: Employee
Measure: Attendance %
```

**3. KPI Comparison**
```
Row: Employee
Column: Week Number
Measure: Total Tickets, Total Calls, Total Billable Hours
```

### Graph View

**Line Chart - Performance Trend**:
- X-axis: Week Number
- Y-axis: Weekly KPI %
- Group By: Employee
- Shows: Performance trends across weeks

**Bar Chart - Weekly Comparison**:
- X-axis: Employee
- Y-axis: Total Billable Hours
- Group By: Week Number
- Shows: Comparison across sprints

### Calendar View

**Month View**:
- Shows weekly records as events
- Color-coded by employee
- Hover to see attendance % and KPI %
- Click to open details

---

## Use Cases

### 1. Sprint Planning (Agile Teams)

**Scenario**: Plan next sprint based on historical data

**Steps**:
1. Filter: Last 4 Weeks
2. Group By: Employee
3. Analyze: Average tickets per sprint
4. Plan: Set realistic sprint goals

**Example**:
```
John Doe - Last 4 Sprints:
Sprint_7: 45 tickets, 95% KPI
Sprint_8: 48 tickets, 96% KPI
Sprint_9: 52 tickets, 102% KPI
Sprint_10: 45 tickets, 95% KPI

Average: ~47.5 tickets per sprint
Next Sprint Target: 50 tickets (realistic)
```

### 2. Weekly Team Review

**Scenario**: Manager reviews team performance

**Steps**:
1. Filter: Current Week
2. View: List of all employees
3. Check: Attendance % and KPI %
4. Identify: Who needs support

**Example**:
```
Sprint_10 Review:
✅ 8/10 employees at 90%+ attendance
✅ 7/10 employees met KPI targets
⚠️  2 employees need support (attendance < 80%)
⚠️  3 employees slightly below target (85-95% KPI)
```

### 3. Performance Trending

**Scenario**: Track employee improvement over time

**Steps**:
1. Open employee record
2. Go to "Weekly Attendance & KPI Records" section
3. View last 8-12 weeks
4. Analyze trend

**Example**:
```
Jane Smith - 8 Week Trend:
Sprint_3: 75% attendance, 80% KPI
Sprint_4: 80% attendance, 85% KPI
Sprint_5: 85% attendance, 88% KPI
Sprint_6: 90% attendance, 92% KPI
Sprint_7: 95% attendance, 95% KPI
Sprint_8: 95% attendance, 98% KPI
Sprint_9: 100% attendance, 100% KPI
Sprint_10: 100% attendance, 102% KPI

Trend: Consistent improvement! 📈
```

### 4. Capacity Planning

**Scenario**: Determine team capacity for upcoming projects

**Steps**:
1. Filter: Last 4 Weeks
2. Calculate: Average billable hours per employee
3. Sum: Total team capacity
4. Plan: Resource allocation

**Example**:
```
Team of 10:
Average per employee: 38 billable hours/week
Total team capacity: 380 hours/week
Available for new project: ~300 hours (buffer for leave/sick)
```

### 5. Leave Pattern Analysis

**Scenario**: Identify leave patterns for better planning

**Steps**:
1. Filter: Last 12 Weeks
2. Pivot: Employee vs Week
3. Measure: Leave Days
4. Identify: Patterns

**Example**:
```
Patterns Identified:
- Fridays have 20% more leave requests
- Sprint_13 had 4 employees on leave (vacation season)
- Average leave days: 0.3 per employee per week
```

---

## Technical Details

### Weekly Record Structure

```python
employee.attendance.kpi.weekly
├── employee_id (Many2one)
├── year (Integer)
├── week_number (Char) - "Sprint_10"
├── week_number_int (Integer) - 10
├── week_start_date (Date)
├── week_end_date (Date)
├── total_days (Integer) - 7
├── Attendance Summary:
│   ├── working_days (Integer)
│   ├── present_days (Integer)
│   ├── absent_days (Integer)
│   ├── leave_days (Integer)
│   ├── weekend_days (Integer)
│   ├── gazetted_days (Integer)
│   └── attendance_percentage (Float)
├── KPI Totals:
│   ├── total_tickets_resolved (Integer)
│   ├── total_calls (Integer)
│   └── total_billable_hours (Integer)
├── KPI Averages:
│   ├── avg_tickets_per_day (Float)
│   ├── avg_calls_per_day (Float)
│   ├── avg_billable_hours_per_day (Float)
│   └── avg_resolution_time (Float)
└── weekly_kpi_percentage (Float)
```

### Computation Methods

**_compute_attendance_summary()**:
```python
# Searches daily records for the week
# Counts by attendance_type
# Calculates working days = total - weekends - holidays
```

**_compute_kpi_totals()**:
```python
# Sums all KPI fields from daily records
# Total tickets, calls, billable hours
```

**_compute_kpi_averages()**:
```python
# Only includes present days
# Divides totals by present_days
# Calculates average per working day
```

**_compute_weekly_kpi_percentage()**:
```python
# Gets weekly targets from hr.employee
# Compares actual totals vs targets
# Uses weighted calculation
# Same logic as daily KPI %
```

### Data Integrity

**SQL Constraint**:
```sql
UNIQUE(employee_id, year, week_number_int)
```
- Ensures one record per employee per week
- Prevents duplicates
- Maintains data integrity

### Performance

**Optimization**:
- Stored computed fields (no real-time computation)
- Indexed fields for fast searching
- Batch processing in scheduled jobs
- Efficient SQL queries

**Expected Performance**:
- Single week generation: < 5 seconds (100 employees)
- 4 weeks update: 15-20 seconds (100 employees)
- View loading: Instant (indexed queries)

---

## Best Practices

### 1. Set Realistic Weekly Targets
- Base on historical data
- Account for leave/holidays
- Review and adjust quarterly
- Consider team capacity

### 2. Regular Reviews
- Weekly team standup
- Monthly performance reviews
- Quarterly target adjustments
- Annual planning sessions

### 3. Data Quality
- Ensure daily records are accurate
- Correct errors promptly
- Run manual updates after bulk changes
- Verify weekly totals periodically

### 4. Consistent Tracking
- Update daily records daily
- Don't batch-enter at week end
- Maintain attendance accuracy
- Log KPIs same day

### 5. Use for Planning
- Sprint capacity planning
- Resource allocation
- Leave scheduling
- Performance forecasting

---

## Troubleshooting

### Issue: Weekly totals don't match manual count

**Cause**: Daily records missing or incorrect
**Fix**: 
1. Check daily records for that week
2. Verify all 7 days have records
3. Click "Refresh Weekly Data"

### Issue: Attendance % seems wrong

**Cause**: Weekend/holiday calculation issue
**Fix**:
1. Verify employee resource calendar
2. Check gazetted holiday configuration
3. Confirm week date range is correct

### Issue: Weekly KPI % shows 0%

**Cause**: No weekly targets set
**Fix**:
1. Open employee record
2. Go to KPI Targets tab
3. Set weekly target fields
4. Refresh weekly record

### Issue: Missing weekly records

**Cause**: Scheduled job not running or no daily data
**Fix**:
1. Check if scheduled job is active
2. Verify daily records exist for that week
3. Manually create: 
```python
env['employee.attendance.kpi.weekly'].create_weekly_records(year=2024, week_number=10)
```

---

## Integration with Daily Records

### Automatic Sync

When daily records change:
1. User updates daily record
2. Daily record saves
3. **Weekly record does NOT auto-update**
4. Weekly scheduled job runs at 2 AM
5. Weekly record refreshes next morning

### Manual Sync

If you need immediate update:
1. Open weekly record
2. Click "Refresh Weekly Data" button
3. Weekly totals recalculate instantly

### Data Source

Weekly records are **read-only aggregations**:
- Data comes from daily records
- Cannot edit weekly totals directly
- Edit daily records to change weekly totals
- Weekly record recalculates automatically

---

## Frequently Asked Questions

**Q: Can I edit weekly totals directly?**
A: No. Weekly records are computed from daily records. Edit the daily records instead.

**Q: How often do weekly records update?**
A: Automatically every day at 2:00 AM. Manual refresh available anytime.

**Q: What if I have incomplete daily data?**
A: Weekly record still generates, but totals will be partial. Complete daily data for accurate weekly summaries.

**Q: Can I have different targets per week?**
A: No. Weekly targets are set at employee level. Set average expected performance.

**Q: Do weekends count in calculations?**
A: No. Working days exclude weekends and gazetted holidays.

**Q: What if employee was on leave the whole week?**
A: Working days = 5, Present days = 0, Leave days = 5, Attendance % = 0%

**Q: How far back can I see weekly records?**
A: All historical weeks with daily data. No limit.

**Q: Can I delete weekly records?**
A: HR Managers can delete. Regular users cannot.

---

## Version History

**Version 3.0 (Current)**
- Initial release of weekly records feature
- Automatic weekly aggregation
- Weekly targets and performance tracking
- 4-week automatic updates
- Manual refresh capability

---

## Summary

The **Weekly Records** feature provides:
- ✅ Automatic weekly summaries
- ✅ Attendance % tracking
- ✅ KPI totals and averages
- ✅ Weekly target comparison
- ✅ Sprint-based planning support
- ✅ Comprehensive reporting
- ✅ Trend analysis capabilities

**Perfect for**:
- Agile teams using sprints
- Weekly performance reviews
- Capacity planning
- Attendance monitoring
- KPI tracking and improvement

---

**Weekly Records make it easy to track and improve team performance sprint by sprint!** 🎯📊
