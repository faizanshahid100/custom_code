from odoo import models, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    user_status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ], string='Status', default='active')
