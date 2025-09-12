{
    'name': 'Microsoft Teams',
    'summary': 'Join Microsoft Team Meetings',
    "author": "Farooq Butt | Prime System Solutions",
    "website": "https://primesystemsolutions.com.com",
    "maintainer": "Prime System Solutions",
    'category': 'Meetings',
    "version": "16.0.1.0.0",
    'depends': ['calendar'],
    'license': 'LGPL-3',
    'category': 'Meetings',
    'summary': 'Join Microsoft Team Meetings',
    'description': '''
A Module To Join Team  Meeting in Odoo easily
''',
    'data': [
        'views/res_company_view.xml',
        'views/meeting.xml',
    ],
    "images": [
        'static/description/banner.gif',
        'static/description/icon.png',
    ],
    "auto_install": False,
    "installable": True,
    "application": True,
}
