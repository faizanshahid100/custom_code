{
    'name': 'Customer Service Management Development',
    'version': '1.0',
    'depends': ['hr', 'hr_attendance', 'calendar', 'web'],
    'data': [
        # 'security/security.xml',
        'security/ir.model.access.csv',
        'views/csm_handbook_views.xml',
        'views/res_partner_ext.xml',
        'views/csm_meeting_views.xml',
        'views/csm_dashboard_views.xml',
        'views/menuitems.xml',
        'data/ir_cron_gar_update.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'csm_customization/static/src/css/csm_dashboard.css',
            'csm_customization/static/src/js/csm_dashboard.js',
            'csm_customization/static/src/xml/csm_dashboard.xml',
        ],
    },
    'installable': True,
}
