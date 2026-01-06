from odoo import models, fields, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    work_from_office_ip_1 = fields.Char(string="Work from Office IP ")
    work_from_office_ip_2 = fields.Char(string="Work from Office IP 2")
