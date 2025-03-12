# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class HrContract(models.Model):
    _inherit = 'hr.contract'

    payslip_currency_id = fields.Many2one('res.currency', string="Payslip Currency", readonly=False)
    travel_allowances = fields.Monetary('Travel Allowances', currency_field='payslip_currency_id', tracking=True)
    fuel_allowances = fields.Monetary('Fuel Allowances', currency_field='payslip_currency_id', tracking=True)
    relocation_allowances = fields.Monetary('Relocation Allowances', currency_field='payslip_currency_id', tracking=True)
    wage = fields.Monetary('Wage', currency_field='payslip_currency_id', required=True, tracking=True, help="Employee's monthly gross wage.")
