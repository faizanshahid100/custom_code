from odoo import models, fields

class DailyProgress(models.Model):
    _inherit = 'daily.progress'

    connectwise_id = fields.Many2one(
        'connectwise.timesheet',
        string='ConnectWise Timesheet',
        ondelete='cascade',
        index=True
    )