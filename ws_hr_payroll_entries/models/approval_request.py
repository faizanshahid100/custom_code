# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ApprovalRequestExt(models.Model):
    _inherit = 'approval.request'

    hours = fields.Float(string="Total Hours", compute="_compute_hours", store=True)
    approval_date = fields.Datetime('Approval Date')
    category_sequence_code = fields.Char(related='category_id.sequence_code', store=True,
                                         string="Category Sequence Code")

    @api.depends('date_start', 'date_end')
    def _compute_hours(self):
        for record in self:
            if record.date_start and record.date_end:
                delta = record.date_end - record.date_start
                record.hours = delta.total_seconds() / 3600.0  # Convert seconds to hours
            else:
                record.hours = 0.0

    def action_approve(self, approver=None):
        # To pass the datetime when approvals approved
        res = super(ApprovalRequestExt, self).action_approve(approver)
        self.approval_date = fields.Datetime.now()
        return res