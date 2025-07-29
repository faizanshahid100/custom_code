# -*- coding: utf-8 -*-
{
    'name': "Prime Solutions Custom",
    'summary': """
       """,
    'description': """
    """,
    'author': "M.Ahsan",
    'website': "https://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.3',
    'depends': ['base', 'mail', 'project', 'web', 'hr', 'survey'],
    'data': [
        'data/ir_cron_data.xml',
        'data/mail_channel.xml',
        'security/ir.model.access.csv',
        'security/groups.xml',
        'views/res_users.xml',
        'views/daily_progress.xml',
        'views/weekly_report.xml',
        'views/hr_employee.xml',
        'views/hr_attendance_ext.xml',
        'views/employee_feedback.xml',
        'views/meeting_tracker.xml',
        'views/meeting_attendance_summary_views.xml',
        'views/survey_survey_ext.xml',
        'views/survey_user_input_ext.xml',
        'views/score_weightage.xml',
        'views/score_card.xml',
        'views/hr_leave_type_ext.xml',
        'views/weekly_ticket_reports.xml',
        'data/mail_template_data.xml',
        'wizard/meeting_summary_view.xml',
        'wizard/scorecard_wizard.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'prime_sol_custom/static/src/js/csat_validation.js',
            'prime_sol_custom/static/src/xml/*.xml',
            'prime_sol_custom/static/src/css/tree_scorecard.css',
        ],
    },
    'license': 'LGPL-3',
    'installable': True,
    'application': False,

}
