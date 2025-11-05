{
    'name': 'Asset Management System',
    'version': '1.0',
    'summary': 'Manage IT Assets and Assignments',
    'author': 'Farooq Butt | Prime System Solutions',
    'depends': ['base', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/asset_views.xml',
        'views/location_views.xml',
        'views/assignment_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
}
