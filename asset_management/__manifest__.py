{
    'name': 'Asset Management',
    'version': '17.0',
    'summary': 'Manage company assets, transfers, maintenance, and depreciation.',
    'description': """
        Streamline your asset lifecycle management with our comprehensive Odoo module. Track assets, automate depreciation, manage maintenance, and handle transfers effortlessly. Generate detailed reports, monitor warranties, and optimize asset utilization. User-friendly interface ensures easy adoption. Suitable for businesses of all sizes, this module empowers you to make informed decisions and maximize the value of your assets.
    """,
    'category': 'Operations',
    'author': 'WebbyCrown Solutions',
    'website': 'https://www.webbycrown.com',
    'depends': ['base', 'product', 'hr', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/sequence.xml',
        'views/asset_views.xml',
        'views/asset_vendor_views.xml',
        'views/asset_report.xml',
    ],
    'images': ['static/description/main_screenshot.png','static/description/formate_screenshot_1.png','static/description/formate_screenshot_2.png','static/description/formate_screenshot_3.png','static/description/formate_screenshot_4.png','static/description/formate_screenshot_5.png','static/description/formate_screenshot_6.png','static/description/formate_screenshot_7.png'],
    'icon': 'asset_management/static/description/icon.png',
    'application': True,
    'installable': True,
    'price': 0,
    'currency': 'EUR',
    'license': 'LGPL-3',
}
