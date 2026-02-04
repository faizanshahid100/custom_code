{
    'name': 'ConnectWise Timesheet Import',
    'version': '16.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Import ConnectWise Timesheet XML',
    'description': 'Import daily timesheets from ConnectWise XML',
    'depends': ['base', 'hr'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/timesheet_views.xml',
        'views/import_connectwise_xml_views.xml',
    ],
    'installable': True,
    'application': True,
}
