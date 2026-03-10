# -*- coding: utf-8 -*-
{
    'name': 'Employee Attendance & KPI Tracking',
    'version': '16.0.0.1.0',
    'category': 'Human Resources',
    'summary': 'Track employee attendance with daily and weekly KPI monitoring, real-time updates, weighted performance metrics, week/sprint tracking, and automatic retroactive updates',
    'description': """
        Employee Attendance & KPI Tracking
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
        'views/employee_attendance_kpi_weekly_business_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
