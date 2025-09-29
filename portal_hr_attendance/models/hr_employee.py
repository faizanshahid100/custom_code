# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    has_portal_access = fields.Boolean(
        'Portal Access Enabled',
        default=False,
        help="Enable portal access for this employee to view attendance data"
    )
    portal_notifications = fields.Boolean(
        'Enable Portal Notifications', 
        default=True,
        help="Enable email notifications for attendance-related portal activities"
    )

    @api.model
    def get_portal_employee(self, user_id=None):
        """Get employee record for portal user"""
        if not user_id:
            user_id = self.env.user.id
            
        employee = self.search([('user_id', '=', user_id)], limit=1)
        if not employee:
            raise UserError(_('No employee record found for this user. Please contact HR.'))
        
        if not employee.has_portal_access:
            raise UserError(_('Portal access is not enabled for your employee record. Please contact HR.'))
            
        return employee

    def get_attendance_summary(self, date_from=None, date_to=None):
        """Get attendance summary for date range"""
        self.ensure_one()
        
        if not date_from:
            date_from = fields.Date.today() - timedelta(days=30)
        if not date_to:
            date_to = fields.Date.today()
            
        domain = [
            ('employee_id', '=', self.id),
            ('check_in', '>=', date_from),
            ('check_in', '<=', date_to)
        ]
        
        attendances = self.env['hr.attendance'].search(domain, order='check_in desc')
        
        total_hours = sum(att.worked_hours for att in attendances if att.worked_hours)
        total_days = len(set(att.check_in.date() for att in attendances))
        
        return {
            'total_hours': total_hours,
            'total_days': total_days,
            'avg_hours_per_day': total_hours / total_days if total_days else 0,
            'attendances': attendances,
        }

    def get_current_attendance_status(self):
        """Get current attendance status for portal display"""
        self.ensure_one()
        
        last_attendance = self.env['hr.attendance'].search([
            ('employee_id', '=', self.id)
        ], limit=1, order='check_in desc')
        
        if not last_attendance:
            return {
                'status': 'checked_out',
                'status_text': _('No attendance records'),
                'last_activity': None,
                'can_emergency_checkout': False,
            }
        
        is_checked_in = not last_attendance.check_out
        status = 'checked_in' if is_checked_in else 'checked_out'
        
        # Check if emergency checkout is needed (stuck for more than 24 hours)
        can_emergency_checkout = False
        if is_checked_in:
            hours_since_checkin = (fields.Datetime.now() - last_attendance.check_in).total_seconds() / 3600
            can_emergency_checkout = hours_since_checkin > 24
        
        return {
            'status': status,
            'status_text': _('Checked In') if is_checked_in else _('Checked Out'),
            'last_activity': last_attendance.check_out or last_attendance.check_in,
            'can_emergency_checkout': can_emergency_checkout,
            'last_attendance': last_attendance,
        }

    def emergency_checkout(self):
        """Emergency checkout for stuck attendance records"""
        self.ensure_one()
        
        # Find the last check-in without check-out
        last_attendance = self.env['hr.attendance'].search([
            ('employee_id', '=', self.id),
            ('check_out', '=', False)
        ], limit=1, order='check_in desc')
        
        if not last_attendance:
            raise UserError(_('No active check-in found to checkout.'))
        
        # Check if emergency checkout is warranted (more than 1 hour)
        hours_since_checkin = (fields.Datetime.now() - last_attendance.check_in).total_seconds() / 3600
        if hours_since_checkin < 1:
            raise UserError(_('Emergency checkout can only be used after 1 hour of being checked in.'))
        
        # Set checkout time to now
        last_attendance.check_out = fields.Datetime.now()
        
        # Log the emergency checkout
        self.env['mail.message'].create({
            'subject': _('Emergency Checkout Performed'),
            'body': _('Emergency checkout performed via portal at %s') % fields.Datetime.now(),
            'model': 'hr.employee',
            'res_id': self.id,
            'message_type': 'notification',
        })
        
        return {
            'success': True,
            'message': _('Emergency checkout completed successfully.'),
            'checkout_time': last_attendance.check_out,
        }

    def get_weekly_hours(self):
        """Get hours worked this week"""
        self.ensure_one()
        
        # Get start of week (Monday)
        today = fields.Date.today()
        start_of_week = today - timedelta(days=today.weekday())
        
        summary = self.get_attendance_summary(start_of_week, today)
        return summary['total_hours']

    def get_monthly_hours(self):
        """Get hours worked this month"""
        self.ensure_one()
        
        today = fields.Date.today()
        start_of_month = today.replace(day=1)
        
        summary = self.get_attendance_summary(start_of_month, today)
        return summary['total_hours']

    @api.constrains('user_id', 'has_portal_access')
    def _check_portal_access_user(self):
        """Ensure portal access is only enabled for employees with user accounts"""
        for employee in self:
            if employee.has_portal_access and not employee.user_id:
                raise ValidationError(_('Portal access can only be enabled for employees with user accounts.'))