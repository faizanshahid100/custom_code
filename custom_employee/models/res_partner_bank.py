from odoo import api, fields, models, _


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    iban = fields.Char(string="IBAN")
    swift = fields.Char(string="Swift Code")
    code = fields.Char(string="Code")
    bank_address = fields.Char(string="Bank Address")
