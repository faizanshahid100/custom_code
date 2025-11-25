from odoo import http
from odoo.http import request
import json


class CSMDashboardController(http.Controller):

    @http.route('/csm/dashboard/data', type='json', auth='user')
    def get_dashboard_data(self):
        """Get dashboard data for CSM"""
        dashboard = request.env['csm.dashboard']
        return dashboard.get_dashboard_data()

    @http.route('/csm/widget/data', type='json', auth='user')
    def get_widget_data(self, widget_type, **kwargs):
        """Get specific widget data and return records for tree view"""
        dashboard = request.env['csm.dashboard']
        records = dashboard.get_widget_data(widget_type)
        
        if widget_type in ['red_zone', 'amber_zone', 'green_zone', 'total_meetings']:
            # Return CSM handbook records
            return {
                'model': 'csm.handbook',
                'records': records.ids,
                'domain': [('id', 'in', records.ids)]
            }
        elif widget_type == 'task_escalations':
            # Return task line records
            return {
                'model': 'csm.task.lines', 
                'records': records.ids,
                'domain': [('id', 'in', records.ids)]
            }
        
        return {'model': 'csm.handbook', 'records': [], 'domain': []}
