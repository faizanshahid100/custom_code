{
    'name': 'Gazetted Holidays',
    'version': '1.0',
    'category': 'Human Resources',
    'summary': 'Manage Gazetted Holidays by Country and Year',
    'depends': ['base', 'hr_holidays'],
    'data': [
        'security/ir.model.access.csv',
        'data/approvals.xml',
        'views/gazetted_holiday_views.xml',
        'views/hr_employee_ext.xml',
        'views/approval_request_ext.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
