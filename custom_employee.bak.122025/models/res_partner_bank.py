from odoo import api, fields, models, _


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    iban = fields.Char(string="IBAN")
