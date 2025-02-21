# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    att_date = fields.Date(string='Attendance Date')
    attend_date = fields.Date(string='Date', compute='_compute_attend_date')
    # remarks = fields.Char(string='Remarks')

    @api.depends('check_in')
    def _compute_attend_date(self):
        for line in self:
            line.att_date = line.check_in
            line.attend_date = line.check_in
