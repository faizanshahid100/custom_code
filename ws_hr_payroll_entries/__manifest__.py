# -*- coding: utf-8 -*-
{
    'name': "Payroll Work Entries",

    'summary': """
        Payroll Work Entries
        """,

    'description': """
        Payroll Work Entries
    """,

    'author': "Raza",
    'website': "http://www.raza.com",

    'category': 'Payroll',
    'version': '15.0.0.3',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr_payroll', 'hr_attendance'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/hr_payroll_views.xml',
        'views/hr_rest_day_views.xml',
        'views/hr_attendance.xml',
        'views/hr_contract.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
