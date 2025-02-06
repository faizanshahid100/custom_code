# -*- coding: utf-8 -*-
{
    'name': "Prime Solutions Custom",
    'summary': """
       """,
    'description': """
    """,
    'author': "M.Ahsan",
    'website': "https://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.3',
    'depends': ['base', 'mail', 'project','web'],
    'data': [
        'data/ir_cron_data.xml',
        'security/ir.model.access.csv',
        'security/groups.xml',
        'views/res_users.xml',
        'views/daily_progress.xml',
        'views/weekly_report.xml',
        'views/hr_employee.xml',
        'data/mail_template_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'prime_sol_custom/static/src/js/csat_validation.js',
        ],
    },
    'installable': True,
    'application': False,

}
