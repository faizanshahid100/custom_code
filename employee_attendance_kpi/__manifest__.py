# -*- coding: utf-8 -*-
{
    'name': 'Employee Attendance & KPI Tracking',
    'version': '16.0.0',
    'category': 'Human Resources',
    'summary': 'Track employee attendance with KPI monitoring and weighted performance metrics',
    'description': """
        Employee Attendance & KPI Tracking
        ===================================
        * Daily attendance tracking (Present, Absent, Leave, Weekend, Gazetted Holiday)
        * KPI monitoring from daily progress
        * Weighted KPI percentage calculation
        * Automatic daily record creation
    """,
    'author': 'Farooq Butt | Prime System Slutions',
    'website': 'https://www.primesystemsolutions.com',
    'depends': ['hr', 'base', 'prime_sol_custom'],
    'data': [
        'security/ir.model.access.csv',
        'data/scheduled_action.xml',
        'views/employee_attendance_kpi_views.xml',
        'views/hr_employee_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
