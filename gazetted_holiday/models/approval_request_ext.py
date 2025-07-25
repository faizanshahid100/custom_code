from odoo import fields, models, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError


class ApprovalRequestExt(models.Model):
    _inherit = 'approval.request'

    def action_approve(self, approver=None):
        # Call the original method
        res = super(ApprovalRequestExt, self).action_approve(approver)
        if self.category_id.sequence_code == 'FLOATER':
            attendance = self.env['hr.attendance'].search([
                ('employee_id', '=', self.request_owner_id.employee_id.id),
            ])

            attendance_on_date = attendance.filtered(
                lambda a: a.check_in.date() == self.date.date()
            )
            is_floater_date = self.request_owner_id.employee_id.gazetted_holiday_id.line_ids.filtered(
                lambda l: l.date_from and l.date_to and
                          l.date_from <= self.date.date() <= l.date_to and
                          l.serve_reward == 'floater'
            )
            if attendance_on_date and is_floater_date:
                #TODO to create Floater leave
                print('create floater leave')
            else:
                raise ValidationError(
                    _(f"{self.request_owner_id.name} is not eligible for a Floater. Either Request date is not part of the Gazetted Holiday, or there is no attendance recorded for this date."))
        return res
