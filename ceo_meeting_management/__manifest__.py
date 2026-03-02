{
    'name': 'CEO Meeting Management',
    'version': '16.0.1.0.0',
    'summary': 'CEO Employee Task and Meeting Management',
    'description': """
        Module for CEO to manage tasks and meetings with employees.
        Includes Basic Profile, Current Engagement, Performance Snapshot,
        Touch Points History, Risk & Flags, and Meeting Objectives.
    """,
    'author': 'Custom',
    'category': 'Human Resources',
    'depends': ['base', 'hr', 'custom_employee'],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/ceo_meeting_config_views.xml',
        'views/ceo_meeting_views.xml',
        'views/ceo_meeting_menu.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
