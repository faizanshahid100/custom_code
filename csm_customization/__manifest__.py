{
    'name': 'Customer Service Management Development',
    'version': '1.0',
    'depends': ['hr', 'hr_attendance'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/csm_handbook_views.xml',
        'views/menuitems.xml',
    ],
    'installable': True,
}
