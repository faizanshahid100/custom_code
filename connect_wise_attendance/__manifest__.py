{
    'name': 'ConnectWise Attendance',
    'version': '1.0',
    'category': 'Human Resources',
    'summary': 'ConnectWise attendance form with tag fields',
    'author': "Hasnain Mustafa",
    'depends': ['hr_attendance'],
    'data': [
        'security/ir.model.access.csv',
        'views/connect_wise_attendance_views.xml',
        'wizard/xml_import_wizard_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
