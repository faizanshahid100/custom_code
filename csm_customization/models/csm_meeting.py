from odoo import fields, models


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    csm_handbook_id = fields.Many2one('csm.handbook', string='CSM Handbook')
