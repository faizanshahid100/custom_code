from odoo import api, fields, models


class ResPartnerExt(models.Model):
    _inherit = 'res.partner'


    business_tech = fields.Char(string='Business/Tech')
    current_meeting_frequency = fields.Selection([
        ('monthly', 'Monthly'),
        ('bi_monthly', 'Bi-Monthly'),
        ('weekly', 'Weekly'),
        ('bi_weekly', 'Bi-Weekly'),
        ('tbd', 'TBD'),
        ('not_required', 'Not Required')
    ], string='Current Meeting Frequency')