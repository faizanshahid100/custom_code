from odoo import fields, models, _
from datetime import datetime, timedelta, date
from odoo.exceptions import ValidationError


class ApprovalRequestExt(models.Model):
    _inherit = 'hr.leave.allocation'


    approval_request_id = fields.Many2one('approval.request', string='Approval Request')
