# -*- coding: utf-8 -*-
{
    'name': "Custom Employee",
    'summary': """
        Custom Employee""",

    'description': """
        Custom Employee
    """,

    'author': "Raza Awan",
    'website': 'http://www.abc.com',
    'category': 'All',
    'version': '16.0.0.1',
    'depends': ['base', 'hr', 'hr_holidays'],
    'data': [
        'security/ir.model.access.csv',
        'data/email_template.xml',
        'data/scheduled_action.xml',
        'data/onsite_day.xml',
        'views/employees.xml',
        'views/res_partner_bank.xml',
        'views/hr_employee_pivot.xml',
    ],

}
