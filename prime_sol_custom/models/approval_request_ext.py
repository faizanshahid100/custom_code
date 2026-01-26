# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, Command, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import date

from collections import defaultdict


class DailyProgressExt(models.Model):
    _inherit = 'approval.request'

    employee_email = fields.Char('Employee Email')
    relation = fields.Selection([('self', 'Self'), ('spouse', 'Spouse'), ('son', 'Son'), ('daughter', 'Daughter')],'Relation with Patient')
    remaining_opd = fields.Float(string="Remaining OPD Limit", compute="_compute_remaining_opd", store=False)

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
        elif self.category_id.sequence_code == 'OPD-':
            self._check_opd_yearly_limit()

        return res  # Return the original result if needed

    def action_approve(self, approver=None):
        # Call the original method
        res = super(DailyProgressExt, self).action_approve(approver)

        if self.category_id.sequence_code == 'PMAF':
            # Call the attendance entry method
            self._create_attendance_entry()
        elif self.category_id.sequence_code == 'OPD-':
            self._check_opd_yearly_limit()

        return res  # Return the original result if needed

    def action_withdraw(self, approver=None):
        # Call the original method
        res = super(DailyProgressExt, self).action_withdraw(approver)
        if self.category_id.sequence_code == 'PMAF':
            attendance = self.env['hr.attendance'].search([('approval_request_id', '=', self.id)], limit=1)
            attendance.unlink()
        return res

    def _check_opd_yearly_limit(self):
        for rec in self:
            if not rec.category_id or rec.category_id.sequence_code != "OPD-":
                continue

            if rec.amount <= 0:
                raise ValidationError(_("OPD amount must be greater than zero."))

            year_start = self.date.replace(month=1, day=1)
            year_end = self.date.replace(month=12, day=31)

            approved_opds = self.search([
                ("request_owner_id", "=", rec.request_owner_id.id),
                ("category_id", "=", rec.category_id.id),
                ("request_status", "=", "approved"),
                ("date", ">=", year_start),
                ("date", "<=", year_end),
                ("id", "!=", rec.id),
            ])

            total_used = sum(approved_opds.mapped("amount"))

            # ✅ Allow exactly up to 60,000
            if total_used + rec.amount > 60000:
                raise ValidationError(_(
                    "OPD yearly limit exceeded.\n\n"
                    "Yearly Limit: 60,000\n"
                    "Already Used: %.2f\n"
                    "Requested: %.2f\n"
                    "Remaining Balance: %.2f"
                ) % (
                                          total_used,
                                          rec.amount,
                                          60000 - total_used
                                      ))

    @api.constrains("amount", "category_id", "date")
    def _check_opd_on_change(self):
        self._check_opd_yearly_limit()

    @api.depends('category_id', 'request_owner_id')
    def _compute_remaining_opd(self):
        OPD_LIMIT = 60000

        for record in self:
            record.remaining_opd = 0.0

            # Only for OPD category (ID = 14)
            if record.category_id.id != 14 or not record.request_owner_id:
                continue

            # Current year date range
            today = fields.Date.today()
            start_of_year = date(today.year, 1, 1)
            end_of_year = date(today.year, 12, 31)

            # Sum of OPD amounts already used in current year
            opd_requests = self.env['approval.request'].search([
                ('request_owner_id', '=', record.request_owner_id.id),
                ('category_id', '=', 14),
                ('date', '>=', start_of_year),
                ('date', '<=', end_of_year),
                ('request_status', '=', 'approved')
            ])

            used_amount = sum(opd_requests.mapped('amount'))
            record.remaining_opd = OPD_LIMIT - used_amount