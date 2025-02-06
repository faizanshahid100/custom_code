from PIL.ImageChops import offset
from odoo import models, fields, api, _


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    hour_start_from = fields.Float('Hour Start From', default=0.0)
    total_working_hour = fields.Float('Total Working Hour', default=5.0)

    d_ticket_resolved = fields.Integer('Ticket Resolved')
    d_avg_resolution_time = fields.Integer('Avg.Resolution Time')
    d_CAST = fields.Integer('CAST %')
    d_billable_hours = fields.Integer('Billable Hours')

    ticket_resolved = fields.Integer('Ticket Resolved')
    avg_resolution_time = fields.Integer('Avg.Resolution Time')
    CAST = fields.Integer('CAST %')
    billable_hours = fields.Integer('Billable Hours')

    dayofweek = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
    ], 'Day of Week', compute="_compute_working_days")
