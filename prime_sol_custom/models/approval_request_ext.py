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
            })

    def action_approve(self, approver=None):
        # Call the original method
        res = super(DailyProgressExt, self).action_approve(approver)

        # Call the attendance entry method
        self._create_attendance_entry()

        return res  # Return the original result if needed