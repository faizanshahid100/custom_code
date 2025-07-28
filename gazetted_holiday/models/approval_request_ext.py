from odoo import fields, models, _
from datetime import datetime, timedelta, date
from odoo.exceptions import ValidationError


class ApprovalRequestExt(models.Model):
    _inherit = 'approval.request'

    def action_confirm(self):
        res = super(ApprovalRequestExt, self).action_confirm()
        if self.category_id.sequence_code == 'FLOATER':
            employee = self.request_owner_id.employee_id

            # Generate list of all dates between date_start and date_end
            date_list = [
                self.date_start.date() + timedelta(days=i)
                for i in range((self.date_end.date() - self.date_start.date()).days + 1)
            ]

            # Get attendance records for the date range
            attendances = self.env['hr.attendance'].search([
                ('employee_id', '=', employee.id),
                ('check_in', '>=', self.date_start),
                ('check_in', '<=', self.date_end),
            ])
            attendance_dates = set(a.check_in.date() for a in attendances)

            # Get floater gazetted dates
            floater_dates = set()
            for line in employee.gazetted_holiday_id.line_ids.filtered(lambda l: l.serve_reward == 'floater'):
                if line.date_from and line.date_to:
                    floater_dates.update([
                        line.date_from + timedelta(days=i)
                        for i in range((line.date_to - line.date_from).days + 1)
                    ])

            # Check each date in request range
            for day in date_list:
                if day not in attendance_dates or day not in floater_dates:
                    raise ValidationError(_(
                        f"{employee.name} is not eligible for a Floater. Either date {day.strftime('%d-%m-%Y')} "
                        f"is not part of the Gazetted Floater Holiday or attendance is missing."
                    ))

        return res

    def action_approve(self, approver=None):
        res = super(ApprovalRequestExt, self).action_approve(approver)

        if self.category_id.sequence_code == 'FLOATER':
            floater_leave_type = self.env['hr.leave.type'].search(
                [('name', '=', 'Floater Leaves')], limit=1
            )
            if not floater_leave_type:
                raise ValidationError("Floater Leave type not found. Please create it in Time Off types.")

            floater_leave = self.env['hr.leave.allocation'].sudo().create({
                'name': f'Floater Leave approved by {self.env.user.name}',
                'holiday_status_id': floater_leave_type.id,
                'allocation_type' : 'regular',
                'approval_request_id' : self.id,
                'holiday_type' : 'employee',
                'employee_id': self.request_owner_id.employee_id.id,
                'date_from': date.today().replace(month=1, day=1),
                'number_of_days': (self.date_end - self.date_start).days + 1,
            })
            if floater_leave.state == 'draft':
                floater_leave.action_confirm()
                floater_leave.action_validate()
            elif floater_leave.state == 'confirm':
                floater_leave.action_validate()

        return res

    def action_withdraw(self, approver=None):
        res = super(ApprovalRequestExt, self).action_withdraw(approver)
        if self.category_id.sequence_code == 'FLOATER':
            floater_leave = self.env['hr.leave.allocation'].search([('approval_request_id', '=', self.id)], limit=1)
            floater_leave.action_refuse()
            floater_leave.action_draft()
            floater_leave.unlink()
        return res