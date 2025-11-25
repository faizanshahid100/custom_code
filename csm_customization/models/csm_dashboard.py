from odoo import models, fields, api
from datetime import datetime, timedelta
import json


class CSMDashboard(models.Model):
    _name = 'csm.dashboard'
    _description = 'CSM Dashboard'

    name = fields.Char(string='Dashboard Name', default='CSM Dashboard')

    @api.model
    def get_dashboard_data(self):
        """Get all dashboard widget data"""
        return {
            'total_meetings': self._get_total_meetings(),
            'gar_counts': self._get_gar_counts(),
            'client_satisfaction': self._get_client_satisfaction(),
            'client_feedback': self._get_client_feedback(),
            'employee_pulse': self._get_employee_pulse(),
            'no_show_today': self._get_no_show_today(),
            'client_wise_meetings': self._get_client_wise_meetings(),
            'task_escalations': self._get_task_escalations(),
            'team_overview': self._get_team_overview(),
            'low_performers': self._get_low_performers(),
        }

    def _get_total_meetings(self):
        """Get total number of meetings this month"""
        today = datetime.now()
        start_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        count = self.env['csm.handbook'].search_count([
            ('current_month_schedule', '>=', start_month),
            ('current_month_schedule', '<=', today)
        ])
        return count

    def _get_gar_counts(self):
        """Get GAR status counts"""
        red_count = self.env['csm.handbook'].search_count([('gar', '=', 'red')])
        amber_count = self.env['csm.handbook'].search_count([('gar', '=', 'amber')])
        green_count = self.env['csm.handbook'].search_count([('gar', '=', 'green')])
        
        return {
            'red': red_count,
            'amber': amber_count,
            'green': green_count
        }

    def _get_client_satisfaction(self):
        """Mock client satisfaction data"""
        return {'satisfied': 0, 'total': 114}

    def _get_client_feedback(self):
        """Mock client feedback data"""
        return {
            'positive': 16,
            'total': 114,
            'negative': 1
        }

    def _get_employee_pulse(self):
        """Mock employee pulse meeting data"""
        return {
            'completed': 22,
            'total': 2,
            'pending': 0
        }

    def _get_no_show_today(self):
        """Get no show count for today"""
        today = datetime.now().date()
        count = self.env['csm.handbook'].search_count([
            ('current_month_schedule', '>=', today),
            ('current_month_schedule', '<', today + timedelta(days=1)),
            ('client_attend_call', '=', 'no')
        ])
        return {'no_show': 95, 'total': 145}

    def _get_client_wise_meetings(self):
        """Get client wise meeting data for chart"""
        meetings = self.env['csm.handbook'].read_group(
            [('current_month_schedule', '!=', False)],
            ['customer_id'],
            ['customer_id']
        )
        
        data = []
        for meeting in meetings:
            if meeting['customer_id']:
                data.append({
                    'client': meeting['customer_id'][1],
                    'count': meeting['customer_id_count']
                })
        
        return data

    def _get_task_escalations(self):
        """Get high priority task escalations"""
        tasks = self.env['csm.task.lines'].search([
            ('priority', '=', '3'),
            ('csm_task_confirmed', '=', False)
        ], limit=5)
        
        data = []
        for task in tasks:
            data.append({
                'id': task.id,
                'priority': 'High',
                'reason': task.reason or 'This is the test',
                'assign_date': task.assign_date.strftime('%m/%d/%Y') if task.assign_date else '',
                'last_modified': task.write_date.strftime('%m/%d/%Y %H:%M:%S') if task.write_date else ''
            })
        
        return data

    def _get_team_overview(self):
        """Get team overview data"""
        return [
            {'resource': 'Resource Name', 'tickets': 'Teams / Tickets Resolved'}
        ]

    def _get_low_performers(self):
        """Get low performer data"""
        return [
            {'employee': 'Employee', 'company': 'Company', 'score': 'Cumulative Score'}
        ]

    @api.model
    def get_widget_data(self, widget_type, domain=None):
        """Get specific widget data with optional domain filter"""
        if widget_type == 'red_zone':
            return self.env['csm.handbook'].search([('gar', '=', 'red')])
        elif widget_type == 'amber_zone':
            return self.env['csm.handbook'].search([('gar', '=', 'amber')])
        elif widget_type == 'green_zone':
            return self.env['csm.handbook'].search([('gar', '=', 'green')])
        elif widget_type == 'total_meetings':
            today = datetime.now()
            start_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            return self.env['csm.handbook'].search([
                ('current_month_schedule', '>=', start_month),
                ('current_month_schedule', '<=', today)
            ])
        elif widget_type == 'task_escalations':
            return self.env['csm.task.lines'].search([
                ('priority', '=', '3'),
                ('csm_task_confirmed', '=', False)
            ])
        
        return []
