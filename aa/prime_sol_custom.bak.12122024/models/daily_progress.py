import logging
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class DailyProgress(models.Model):
    _name = "daily.progress"
    _inherit = "mail.thread"
    _description = "Daily Progress"
    _rec_name = 'resource_user_id'

    resource_user_id = fields.Many2one('res.users', string='Resource Name *', default=lambda self: self.env.user.id)
    date_of_project = fields.Date("Today Date", required=True)
    is_admin = fields.Boolean(string='Is Admin', compute='_compute_is_admin')
    ticket_assigned_new = fields.Integer(string='Tasks / Tickets Assigned')
    avg_resolved_ticket = fields.Integer(string='Tasks / Tickets Resolved')
    avg_resolution_time = fields.Integer(string='Avg. Resolution Time (min.)')
    csat_new = fields.Float(string='CSAT %')
    billable_hours = fields.Float(string='Billable Hours %')
    no_calls_duration = fields.Integer(string='Number of Calls Attended')

    @api.depends('resource_user_id')
    def _compute_is_admin(self):
        for record in self:
            record.is_admin = self.env.user.has_group('base.group_system')

    @api.constrains('csat_new', 'avg_resolution_time', 'ticket_assigned_new', 'avg_resolved_ticket', 'billable_hours')
    def _check_values(self):
        for record in self:
            if record.csat_new < 0:
                raise ValidationError('CSAT % must be a positive number.')
            if not (0 <= record.csat_new <= 100):
                raise ValidationError('CSAT % must be between 0 and 100.')
            if len(str(record.csat_new).split('.')[1]) > 2:
                raise ValidationError('CSAT % must have up to two decimal places.')
            if record.avg_resolution_time < 0:
                raise ValidationError('Avg. Resolution Time (min.) must be a positive number.')
            if record.ticket_assigned_new < 0:
                raise ValidationError('Tasks / Tickets Assigned must be a positive number.')
            if record.avg_resolved_ticket < 0:
                raise ValidationError('Tasks / Tickets Resolved must be a positive number.')
            if record.billable_hours < 0:
                raise ValidationError('Billable Hours % must be a positive number.')
            if not (0 <= record.billable_hours <= 100):
                raise ValidationError('Billable Hours % must be between 0 and 100.')
            if len(str(record.billable_hours).split('.')[1]) > 2:
                raise ValidationError('Billable Hours % must have up to two decimal places.')
