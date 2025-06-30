from odoo import models, fields, api
from datetime import datetime, timedelta, date


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'


    approval_request_id = fields.Many2one('approval.request')

    @api.model
    def create(self, vals):
        res = super(HrAttendance, self).create(vals)
        if res:
            check_in_date = datetime.strftime(res.check_in, '%m-%d-%Y')
            current_date = datetime.strftime(datetime.today(), '%m-%d-%Y')
            if res.check_in:
                if check_in_date == current_date:
                    res.employee_id.user_id.user_status = 'active'
        return res

    def write(self, vals):
        res = super(HrAttendance, self).write(vals)
        if self:
            if self.check_out:
                check_out_date = datetime.strftime(self.check_out, '%m-%d-%Y')
                current_date = datetime.strftime(datetime.today(), '%m-%d-%Y')
                if check_out_date == current_date:
                    self.employee_id.user_id.user_status = 'inactive'

                if not self.env.user.has_group('prime_sol_custom.group_late_checkout_attendance'):
                    if self.employee_id.hour_start_from and self.employee_id.total_working_hour:
                        check_in_time = self.check_in + timedelta(hours=5)
                        check_out_time = self.check_out
                        working_hours = timedelta(hours=self.employee_id.total_working_hour)
                        allowed_check_out_time = check_in_time.replace(hour=abs(int(self.employee_id.hour_start_from - 5)), minute=0,
                                                                       second=0) + working_hours
                        if check_out_time > allowed_check_out_time:
                            self.check_out = allowed_check_out_time
        return res

    def _check_checkin_checkout_attendance(self):
        # Email for missing check_out
        today = datetime.today()
        previous_day = today - timedelta(days=1)
        if previous_day.weekday() >= 5:
            return

        previous_day_start = previous_day.replace(hour=0, minute=0, second=0, microsecond=0)
        previous_day_end = previous_day.replace(hour=23, minute=59, second=59, microsecond=999999)
        attendances = self.env['hr.attendance'].search([
            ('create_date', '>=', previous_day_start),
            ('create_date', '<=', previous_day_end)
        ])
        for rec in attendances:
            if not rec.check_in or not rec.check_out:
                template = self.env.ref('prime_sol_custom.mail_template_daily_attendance_check')
                template.send_mail(rec.id, force_send=True)

    def _check_absent_attendance(self):
        # Email for absent employee attendance
        today = datetime.today()
        previous_day = today - timedelta(days=1)
        if previous_day.weekday() >= 5:
            return

        previous_day_start = previous_day.replace(hour=0, minute=0, second=0, microsecond=0)
        previous_day_end = previous_day.replace(hour=23, minute=59, second=59, microsecond=999999)
        all_employees = self.env['hr.employee'].search([])
        attendances = self.env['hr.attendance'].search([
            ('create_date', '>=', previous_day_start),
            ('create_date', '<=', previous_day_end)
        ])
        attended_employee_ids = attendances.mapped('employee_id.id')
        absent_employees = all_employees.filtered(lambda e: e.id not in attended_employee_ids)
        for rec in absent_employees:
            template = self.env.ref('prime_sol_custom.mail_template_daily_attendance_no_mark')
            template.send_mail(rec.id, force_send=True)

    @api.model
    def _auto_checkout_employees(self):
        time_limit = timedelta(hours=9, minutes=15)
        now = fields.Datetime.now()

        attendances = self.search([
            ('check_out', '=', False),
            ('check_in', '!=', False)
        ])

        for att in attendances:
            elapsed = now - att.check_in
            if elapsed >= time_limit:
                att.check_out = att.check_in + time_limit