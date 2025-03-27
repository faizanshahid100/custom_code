# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, Command, fields, models, _
from odoo.exceptions import UserError, ValidationError

from collections import defaultdict


class DailyProgressExt(models.Model):
    _inherit = 'approval.request'

    def _create_attendance_entry(self):
        """Creates an attendance entry for the request owner if they are an employee."""
        employee = self.request_owner_id.employee_id
        if employee and self.date_start and self.date_end:
            self.env['hr.attendance'].create({
                'employee_id': employee.id,
                'check_in': self.date_start,
                'check_out': self.date_end,
                'approval_request_id': self.id,
            })

    def action_confirm(self):
        # Call the original method
        res = super(DailyProgressExt, self).action_confirm()
        if self.category_id.sequence_code == 'PMAF':
            time_diff = (self.date_end - self.date_start).total_seconds() / 3600
            if time_diff > 9:
                raise ValidationError(_("The time difference between Start Time and End Time cannot exceed 9 hours."))
            # Call the attendance entry method

        return res  # Return the original result if needed

    def action_approve(self, approver=None):
        # Call the original method
        res = super(DailyProgressExt, self).action_approve(approver)

        if self.category_id.sequence_code == 'PMAF':
            # Call the attendance entry method
            self._create_attendance_entry()

        return res  # Return the original result if needed

    def action_withdraw(self, approver=None):
        # Call the original method
        res = super(DailyProgressExt, self).action_withdraw(approver)
        if self.category_id.sequence_code == 'PMAF':
            attendance = self.env['hr.attendance'].search([('approval_request_id', '=', self.id)], limit=1)
            attendance.unlink()
        return res
