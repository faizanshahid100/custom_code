from odoo import models, fields, api
from datetime import datetime

class DynamicProgress(models.Model):
    _name = "dynamic.progress"
    _rec_name = "resource_user_id"
    _description = "Dynamic Progress Tracking"

    date = fields.Date(string='Date*', required=True, default=fields.Date.today())
    resource_user_id = fields.Many2one('res.users', required=True, string='Resource Name *', default=lambda self: self.env.user.id)
    shift = fields.Char(string='Shift Type*', required=True)
    task = fields.Char(string='Task', required=True)
    assigned = fields.Char(string='Assigned By*',required=True)
    project = fields.Char(string='Project*', required=True)
    start_time = fields.Datetime(string='Start Time*', required=True)
    end_time = fields.Datetime(string='End Time*', required=True)
    total_hours = fields.Float(string='Total Hours', compute='_compute_total_hours', store=True)
    comment = fields.Text(string='Comment')

    @api.depends('start_time', 'end_time')
    def _compute_total_hours(self):
        for record in self:
            if record.start_time and record.end_time:
                delta = record.end_time - record.start_time
                record.total_hours = delta.total_seconds() / 3600
            else:
                record.total_hours = 0
