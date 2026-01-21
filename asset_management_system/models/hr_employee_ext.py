from odoo import api, fields, models


class HREmployeeExt(models.Model):
    _inherit = 'hr.employee'

    assigned_asset_ids = fields.One2many('asset.management.asset', 'employee_id', string='Assigned Assets')