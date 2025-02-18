# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class HrContract(models.Model):
    _inherit = 'hr.contract'

    travel_allowances = fields.Monetary('Travel Allowances', tracking=True)
    fuel_allowances = fields.Monetary('Fuel Allowances', tracking=True)
    relocation_allowances = fields.Monetary('Relocation Allowances', tracking=True)
