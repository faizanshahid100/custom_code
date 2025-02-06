# -*- coding: utf-8 -*-
{
    'name': "Custom Credentials",
    'summary': """
        Some Extra custom fields for payslip rules""",
    'description': """
        Long description of module's purpose
    """,
    'author': "M.Ahsan",
    'website': "https://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',
    'images': ['static/description/xnrel.png'],
    'depends': ['base','mail','project'],
    'data': [
        'security/ir.model.access.csv',
        'views/custom_credentials.xml',
    ],

    'installable': True,
    'application': False,

}
