# Week/Sprint Number Feature

## Overview
The Employee Attendance KPI module now includes automatic week/sprint number tracking for all records. Each record is automatically tagged with its corresponding week number in the format **Sprint_1**, **Sprint_2**, etc.

## How It Works

### Automatic Calculation
- Week numbers are calculated automatically based on the **date** field
- Uses **ISO 8601** week numbering standard:
  - Week starts on **Monday**
  - Week 1 is the first week with a Thursday
  - Weeks are numbered 1-53
- Format: **Sprint_X** where X is the ISO week number

### Examples
```
Date: Monday, January 1, 2024    → Sprint_1
Date: Tuesday, January 9, 2024   → Sprint_2
Date: Friday, February 16, 2024  → Sprint_7
Date: Monday, December 30, 2024  → Sprint_1 (next year)
```

## Fields Added

### 1. week_number (Char)
- **Format**: "Sprint_1", "Sprint_2", etc.
- **Type**: Computed, Stored
- **Display**: Shown in all views
- **Use**: For display and grouping

### 2. week_number_int (Integer)
- **Format**: 1, 2, 3, etc.
- **Type**: Computed, Stored
- **Display**: Hidden (technical field)
- **Use**: For sorting and filtering

## Usage

### In List View
The week/sprint number is displayed as a column:
```
Date        | Week/Sprint | Employee      | Attendance Type
2024-03-01  | Sprint_9    | John Doe     | Present
2024-03-02  | Sprint_9    | John Doe     | Present
2024-03-11  | Sprint_11   | John Doe     | Present
```

### In Form View
The week/sprint is shown in the Basic Information section:
```
Employee:         John Doe
Date:             2024-03-01
Week/Sprint:      Sprint_9
Attendance Type:  Present
```

### Group By Week/Sprint
You can group records by week in the list view:
1. Click the **Group By** dropdown
2. Select **Week/Sprint**
3. Records are organized by sprint

**Example Grouped View:**
```
▼ Sprint_9
  - John Doe (2024-03-01)
  - Jane Smith (2024-03-01)
  - John Doe (2024-03-02)
  
▼ Sprint_10
  - John Doe (2024-03-08)
  - Jane Smith (2024-03-09)
```

### Filter by Week/Sprint
You can search for specific sprints:
1. In the search box, type: **Sprint_9**
2. All records from week 9 will be shown

### Pivot Analysis by Week
The pivot view now includes week as a dimension:
```
                | Sprint_9  | Sprint_10 | Sprint_11
Employee        | KPI %     | KPI %     | KPI %
----------------|-----------|-----------|----------
John Doe        | 85.5%     | 90.2%     | 88.7%
Jane Smith      | 92.3%     | 89.1%     | 91.5%
```

## Use Cases

### 1. Sprint Planning
Track employee performance by sprint:
```
Pivot View:
- Row: Employee
- Row: Week/Sprint
- Measure: KPI Percentage (Average)
```

### 2. Weekly Reports
Generate reports for specific weeks:
```
Filter: week_number = "Sprint_10"
Group By: Employee
Show: Attendance Type, KPI Performance
```

### 3. Trend Analysis
Compare performance across sprints:
```
Graph View:
- X-axis: Week/Sprint
- Y-axis: KPI Percentage
- Group by: Employee
```

### 4. Team Retrospectives
Review team attendance and KPIs by sprint:
```
Search: Sprint_9
Group By: Attendance Type
Analyze: Present vs Absent patterns
```

## Technical Details

### Computation Method
```python
@api.depends('date')
def _compute_week_number(self):
    """
    Compute week number in format Sprint_X based on ISO week number
    Week starts on Monday (ISO standard)
    """
    for record in self:
        if record.date:
            # Get ISO week number (1-53)
            iso_year, iso_week, iso_weekday = record.date.isocalendar()
            
            # Format as Sprint_X
            record.week_number = f"Sprint_{iso_week}"
            record.week_number_int = iso_week
        else:
            record.week_number = "Sprint_0"
            record.week_number_int = 0
```

### ISO Week Numbering
**Why ISO 8601?**
- International standard
- Consistent year-to-year
- Week always starts on Monday
- Each week belongs to a single year

**Rules:**
1. Week starts on Monday
2. Week 1 is the first week with a Thursday
3. This ensures each year has 52 or 53 complete weeks
4. December 29-31 may be in week 1 of the next year
5. January 1-3 may be in week 52/53 of the previous year

### Example Edge Cases
```
Date: Monday, Dec 30, 2024    → Sprint_1 (2025)
Date: Thursday, Jan 1, 2024   → Sprint_1 (2024)
Date: Sunday, Jan 3, 2024     → Sprint_52 (2023)
```

## Reports Enhanced

All standard reports now support week/sprint:

### 1. Attendance & KPI List
- **Column**: Week/Sprint
- **Group By**: Available
- **Filter**: Searchable

### 2. Pivot Analysis
- **Dimension**: Week/Sprint (row or column)
- **Measure**: All KPIs
- **Drill-down**: Employee → Week → Day

### 3. Graph/Chart
- **Axis**: Week/Sprint
- **Series**: KPI Performance, Attendance
- **Compare**: Multiple employees

### 4. Calendar View
- **Display**: Shows week/sprint on hover
- **Color**: By attendance type
- **Info**: Employee, Week, KPI %

## Custom Queries

### Find All Records for a Sprint
```python
records = env['employee.attendance.kpi'].search([
    ('week_number', '=', 'Sprint_10')
])
```

### Get All Sprints for an Employee
```python
records = env['employee.attendance.kpi'].search([
    ('employee_id', '=', employee_id)
])
sprints = records.mapped('week_number')
unique_sprints = list(set(sprints))
```

### Calculate Average KPI by Sprint
```python
records = env['employee.attendance.kpi'].read_group(
    [('employee_id', '=', employee_id)],
    ['kpi_percentage:avg'],
    ['week_number']
)
```

### Compare Two Sprints
```python
sprint_9 = env['employee.attendance.kpi'].search([
    ('week_number', '=', 'Sprint_9'),
    ('employee_id', '=', employee_id)
])
avg_kpi_9 = sum(sprint_9.mapped('kpi_percentage')) / len(sprint_9)

sprint_10 = env['employee.attendance.kpi'].search([
    ('week_number', '=', 'Sprint_10'),
    ('employee_id', '=', employee_id)
])
avg_kpi_10 = sum(sprint_10.mapped('kpi_percentage')) / len(sprint_10)

improvement = avg_kpi_10 - avg_kpi_9
```

## Configuration

### Change Week Start Day (Advanced)
If you want to use a different week start day (e.g., Sunday):

**Not recommended** - ISO standard is best for consistency, but if needed:
```python
# Custom implementation would require:
# 1. Override _compute_week_number method
# 2. Use custom week calculation logic
# 3. Update documentation
```

### Custom Sprint Names
To change from "Sprint_X" to custom format:

**Method 1: Modify compute method**
```python
# In employee_attendance_kpi.py, change:
record.week_number = f"Sprint_{iso_week}"
# To:
record.week_number = f"Week_{iso_week}"
# Or:
record.week_number = f"W{iso_week}"
```

**Method 2: Add custom field**
```python
sprint_name = fields.Char(
    string='Custom Sprint Name',
    help='Custom name for this sprint/week'
)
```

## Best Practices

### 1. Consistent Sprint Naming
- Stick with the default "Sprint_X" format
- Don't manually override week numbers
- Let the system calculate automatically

### 2. Sprint-Based Planning
- Use week/sprint for Agile teams
- Plan KPIs and targets by sprint
- Review performance at sprint boundaries

### 3. Reporting
- Group by sprint for weekly reviews
- Compare sprints for trend analysis
- Use pivot for multi-dimensional analysis

### 4. Data Entry
- Week numbers update automatically
- No manual entry needed
- Retroactive updates preserve week numbers

## Frequently Asked Questions

**Q: Why does Dec 30 show as Sprint_1?**
A: ISO 8601 standard - it's the first week of the next year.

**Q: Can I change the week start day?**
A: Not recommended. ISO standard (Monday) is international best practice.

**Q: How do I filter by current week?**
A: Use the "This Week" filter, or search for the current sprint number.

**Q: Can I rename sprints?**
A: You can modify the compute method, but keep consistent naming.

**Q: Do retroactive updates preserve week numbers?**
A: Yes! Week numbers are computed from the date automatically.

**Q: Can I export data grouped by sprint?**
A: Yes! Group by week/sprint, then export the list view.

## Troubleshooting

### Issue: Wrong week number
**Cause**: Date calculation or timezone issue
**Fix**: Week numbers are based on ISO 8601 - verify date is correct

### Issue: Week numbers not showing
**Cause**: Field not computed or module not upgraded
**Fix**: Upgrade module, or manually trigger compute

### Issue: Can't group by week
**Cause**: Search view not updated
**Fix**: Upgrade module views

## Version History

**Version 2.1.0**
- Added week_number field (Sprint_X format)
- Added week_number_int for technical operations
- Updated all views to show week/sprint
- Added group by week/sprint
- Added filter by week/sprint
- Enhanced pivot analysis with week dimension

---

**Week/Sprint tracking makes it easy to analyze employee performance and attendance patterns by sprint or week, perfect for Agile teams and sprint-based planning!** 🎯
