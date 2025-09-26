# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import datetime, date, time, timedelta
import pytz

class AttendanceDashboard(models.Model):
    _name = 'attendance.dashboard'
    _description = 'Employees missing check-in after duty start + 20 minutes'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    duty_start = fields.Datetime(string='Duty Start (UTC)', required=True)
    threshold = fields.Datetime(string='Threshold (UTC)', required=True)
    check_in = fields.Datetime(string='Check-In (first today)', readonly=True)
    minutes_overdue = fields.Integer(string='Minutes Overdue', readonly=True)
    hours_overdue = fields.Integer(string='Hours Overdue', readonly=True)
    is_missing = fields.Boolean(string='Missing', default=False)

    @api.model
    def refresh(self):
        """Populate attendance.dashboard with employees missing check-in for today."""
        # clear previous
        self.sudo().search([]).unlink()

        # Use user's timezone for computing local duty times
        tz_name = self.env.user.tz or 'UTC'
        user_tz = pytz.timezone(tz_name)
        now_utc = datetime.now()

        # today in user's tz
        today_local = fields.Date.context_today(self.env.user)

        # get employees who have some duty start time
        employees = self.env['hr.employee'].sudo().search([('hour_start_from', '>', 0.0)])

        for emp in employees:
            # build today's duty start in user's timezone
            hour_float = float(emp.hour_start_from or 0.0)
            hours = int(hour_float)
            minutes = int(round((hour_float - hours) * 60))

            # build naive local datetime and localize
            duty_local_naive = datetime.combine(today_local, time(hours, minutes))
            try:
                duty_local = user_tz.localize(duty_local_naive)
            except Exception:
                # fallback if already aware or DST issues
                duty_local = user_tz.localize(duty_local_naive, is_dst=None)

            # convert to UTC for storing & searching
            duty_utc = duty_local.astimezone(pytz.utc)
            threshold_utc = duty_utc + timedelta(minutes=20)

            # if now hasn't reached threshold yet, skip
            if now_utc <= threshold_utc:
                continue

            # search for any attendance check_in for this employee today (>= local day start)
            day_start_local = datetime.combine(today_local, time(0, 0))
            day_start_utc = user_tz.localize(day_start_local).astimezone(pytz.utc)
            day_start_utc_str = fields.Datetime.to_string(day_start_utc)

            attendance = self.env['hr.attendance'].sudo().search([
                ('employee_id', '=', emp.id),
                ('check_in', '>=', day_start_utc_str)
            ], order='check_in asc', limit=1)

            # if no attendance found today -> create dashboard entry (missing)
            if not attendance:
                minutes_overdue = int((now_utc - threshold_utc).total_seconds() // 60)
                self.sudo().create({
                    'employee_id': emp.id,
                    'duty_start': fields.Datetime.to_string(duty_utc),
                    'threshold': fields.Datetime.to_string(threshold_utc),
                    'check_in': False,
                    'minutes_overdue': minutes_overdue,
                    'hours_overdue': minutes_overdue//60,
                    'is_missing': True,
                })
        return True

    def action_manual_refresh(self):
        """Button to refresh from UI for testing"""
        return self.env['attendance.dashboard'].refresh()
