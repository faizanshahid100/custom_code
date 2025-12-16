# -*- coding: utf-8 -*-

{
    'name': 'Geolocation in HR Attendance',
    'version': '16.0.1.0.1',
    'summary': "The attendance location of the employee",
    'description': "This module helps to identify the checkin/out location of the employee",
    'author': 'Farooq Butt | Prime System Solutions',
    'maintainer': 'Farooq Butt | Prime System Solutions',
    'company': 'Farooq Butt | Prime System Solutions',
    'website': 'https://www.primesystemsolutions.com',
    'category': 'Human Resources',
    'depends': ['base', 'hr', 'hr_attendance'],
    'data': [
        'security/security.xml',
        'views/hr_attendance_views.xml',
    ],

    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}

# Below will be uncomment and add in manifest when location started
# 'assets': {
#     'web.assets_backend': [
#         'odoo_attendance_user_location/static/src/js/my_attendances.js',
#     ],
# },
# 'external_dependencies': {'python': ['geopy']},
