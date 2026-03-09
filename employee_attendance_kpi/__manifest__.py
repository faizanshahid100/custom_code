# -*- coding: utf-8 -*-
{
    'name': 'Employee Attendance & KPI Tracking',
    'version': '16.0.3.1.0',
    'category': 'Human Resources',
    'summary': 'Track employee attendance with daily and weekly KPI monitoring, real-time updates, weighted performance metrics, week/sprint tracking, and automatic retroactive updates',
    'description': """
        Employee Attendance & KPI Tracking
        ===================================
        * Daily attendance tracking (Present, Absent, Leave, Weekend, Gazetted Holiday)
        * **Weekly attendance and KPI summaries** with real-time updates
        * KPI monitoring from daily progress
        * Weighted KPI percentage calculation
        * **Week/Sprint number tracking** (Sprint_1, Sprint_2, etc.)
        * **Real-time weekly record updates** (NEW in v3.1)
        * Automatic daily and weekly record creation
        * Automatic 30-day retroactive updates
        * Real-time updates when attendance/KPI data is entered for past dates
        * Manual update options for administrators
        * Smart triggers on hr.attendance, hr.leave, and daily.progress
        
        Version 3.1 Features
        --------------------
        - **Real-time weekly updates**: Weekly records automatically update when:
          • Daily attendance KPI records change
          • Attendance (check-in/check-out) is added/modified/deleted
          • KPI data (daily.progress) is added/modified/deleted
          • Leave/Time-off is approved/modified/deleted
          • Any daily data affecting the week changes
        - Instant weekly record creation when daily data is entered
        - No waiting for scheduled job - updates happen immediately
        - Weekly records stay synchronized with daily data in real-time
        
        Version 3.0 Features
        --------------------
        - Weekly attendance summaries with working days, present, absent, leave breakdown
        - Weekly KPI totals (sum of week)
        - Weekly KPI averages (per working day)
        - Weekly targets and performance tracking
        - Attendance percentage calculation
        - Automatic weekly record generation from daily records
        - Compare weekly performance against weekly targets
        - Group and filter by week/sprint
        - Weekly analytics and pivot reports
        
        Version 2.1 Features
        --------------------
        - Week/Sprint number field (based on ISO week)
        - Group by week/sprint in reports
        - Filter by week/sprint
        - Week-based analytics in pivot view
        
        Version 2.0 Features
        --------------------
        - Automatic update of last 30 days when scheduled job runs
        - Real-time record updates when users add/modify attendance for past dates
        - Real-time KPI data refresh when daily progress is entered for past dates
        - Manual update action for administrators
        - Comprehensive logging and error handling
        - Performance optimized for bulk updates
    """,
    'author': 'Farooq Butt | Prime System Slutions',
    'website': 'https://www.primesystemsolutions.com',
    'depends': ['hr', 'hr_holidays', 'base', 'prime_sol_custom'],
    'data': [
        'security/ir.model.access.csv',
        'data/scheduled_action.xml',
        'views/employee_attendance_kpi_views.xml',
        'views/employee_attendance_kpi_weekly_views.xml',
        'views/hr_employee_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
