# -*- coding: utf-8 -*-
{
    'name': 'Portal HR Attendance',
    'version': '16.0.1.0.0',
    'category': 'Human Resources/Attendances',
    'summary': 'Portal access for employee attendance self-service',
    'description': """
Portal HR Attendance
===================

This module provides portal users with attendance self-service capabilities including:
- View attendance dashboard with current status
- Browse attendance history with filtering and export
- Emergency check-out functionality
- Request attendance corrections
- Mobile-responsive design

Part of a hybrid attendance system where kiosk stations handle physical check-in/out
and portal provides self-service features for employees who need online access.
    """,
    'author': 'Farooq Butt',
    'website': 'https://abc.com',
    'depends': [
        'base',
        'hr',
        'hr_attendance', 
        'portal',
    ],
    'data': [
        'security/portal_security.xml',
        'security/ir.model.access.csv',
        'views/hr_employee_views.xml',
        'views/portal_attendance_simple.xml',
        'views/portal_menu.xml',
        'data/portal_data.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
