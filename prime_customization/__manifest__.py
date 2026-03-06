{
    'name': 'Prime Customization',
    'version': '1.0',
    'depends': ['base', 'hr'],
    'data': [
        'views/res_partner_ext_views.xml',
    ],
    'external_dependencies': {
        'python': ['xlsxwriter'],
    },
    'installable': True,
}
