# -*- coding: utf-8 -*-
{
    'name': 'Weekly KPI Achievement',
    'version': '16.0.1.0.0',
    'summary': 'Weekly KPI scoring per employee — KPI, Billable, and N/A types',
    'description': """
        Tracks weekly KPI achievement for each employee based on their
        kpi_measurement type (kpi / billable / na).

        - KPI employees: scored on ticket_resolved, CAST, avg_resolution_time
          with equal weight distribution based on number of active targets.
        - Billable employees: scored purely on average billable hours %.
        - N/A employees: no scoring applied.

        Records are auto-generated every Monday via scheduled action.
    """,
    'category': 'Human Resources',
    'author': 'Custom',
    'depends': [
        'hr',
        'mail',
        'prime_sol_custom',
        'sdm_customization',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/cron.xml',
        'views/weekly_kpi_views.xml',
        'views/weekly_business_kpi_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
