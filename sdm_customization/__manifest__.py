{
    'name': 'Attendance Dashboard (Missing Check-in)',
    'version': '1.0',
    'depends': ['hr', 'hr_attendance'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/attendance_dashboard_views.xml',
        'data/ir_cron_attendance_dashboard.xml',
        'views/menuitems.xml',
    ],
    'installable': True,
}
