# -*- coding: utf-8 -*-
{
    'name': "Missing Attendance approval",

    'summary': """
        Missing attendance approval hierarchy""",

    'description': """
        Missing attendance approval hierarchy
    """,

    'author': "Farooq Butt | PrimeSystem",
    'category': 'HR',
    'version': '16.0.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr', 'hr_attendance'],

    # always loaded
    'data': [
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'views/leave_attendance.xml',
    ],

}
