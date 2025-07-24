{
    'name': 'Gazetted Holidays',
    'version': '1.0',
    'category': 'Human Resources',
    'summary': 'Manage Gazetted Holidays by Country and Year',
    'depends': ['base', 'hr_holidays'],
    'data': [
        'security/ir.model.access.csv',
        'views/gazetted_holiday_views.xml',
    ],
    'installable': True,
    'application': False,
}
