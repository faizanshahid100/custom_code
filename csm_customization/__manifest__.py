{
    'name': 'Customer Service Management Development',
    'version': '1.0',
    'depends': ['hr', 'hr_attendance', 'calendar'],
    'data': [
        # 'security/security.xml',
        'security/ir.model.access.csv',
        'views/csm_handbook_views.xml',
        'views/res_partner_ext.xml',
        'views/csm_meeting_views.xml',
        'views/menuitems.xml',
    ],
    'installable': True,
}
