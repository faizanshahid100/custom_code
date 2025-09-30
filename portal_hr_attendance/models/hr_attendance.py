# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    def get_portal_display_data(self):
        """Get attendance data formatted for portal display"""
        self.ensure_one()
        
        return {
            'id': self.id,
            'check_in': self.check_in,
            'check_out': self.check_out,
            'worked_hours': self.worked_hours,
            'check_in_display': self.check_in.strftime('%I:%M %p') if self.check_in else '',
            'check_out_display': self.check_out.strftime('%I:%M %p') if self.check_out else _('Still working'),
            'date_display': self.check_in.strftime('%B %d, %Y') if self.check_in else '',
            'hours_display': self._format_hours(self.worked_hours) if self.worked_hours else _('In progress'),
            'status': 'complete' if self.check_out else 'active',
            'status_class': 'success' if self.check_out else 'warning',
        }

    def _format_hours(self, hours):
        """Format hours for display"""
        if not hours:
            return '0h 0m'
        
        hours_int = int(hours)
        minutes = int((hours - hours_int) * 60)
        
        return f'{hours_int}h {minutes}m'

    @api.model
    def get_attendance_for_export(self, employee_id, date_from, date_to, format_type='csv'):
        """Get attendance records formatted for export"""
        domain = [
            ('employee_id', '=', employee_id),
            ('check_in', '>=', date_from),
            ('check_in', '<=', date_to)
        ]
        
        attendances = self.search(domain, order='check_in desc')
        
        export_data = []
        for attendance in attendances:
            export_data.append({
                'date': attendance.check_in.strftime('%Y-%m-%d'),
                'check_in': attendance.check_in.strftime('%H:%M:%S'),
                'check_out': attendance.check_out.strftime('%H:%M:%S') if attendance.check_out else 'Still working',
                'worked_hours': f'{attendance.worked_hours:.2f}' if attendance.worked_hours else '0.00',
                'status': 'Complete' if attendance.check_out else 'In Progress'
            })
        
        return export_data