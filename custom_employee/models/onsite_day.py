from odoo import models, api, fields

class OnsiteDay(models.Model):
    _name = 'hr.onsite.day'
    _description = 'Onsite Day'

    name = fields.Char(string='Day')