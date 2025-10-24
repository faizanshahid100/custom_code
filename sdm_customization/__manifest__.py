{
    'name': 'Service Delivery Management Development',
    'version': '1.0',
    'depends': ['hr', 'hr_attendance'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/attendance_dashboard_views.xml',
        'data/ir_cron_attendance_dashboard.xml',
        'views/employee_probation_meeting.xml',
        'views/employee_pulse_profile.xml',
        'views/attendance_late_record.xml',
        'views/hr_employee_ext.xml',
        'views/menuitems.xml',
    ],
    'installable': True,
}
