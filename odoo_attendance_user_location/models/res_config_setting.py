from odoo import models, fields, _

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    work_from_office_ip_1 = fields.Char(
        string="Work from Office IP ",
        related='company_id.work_from_office_ip_1',
        readonly=False
    )
    work_from_office_ip_2 = fields.Char(
        string="Work from Office IP 1",
        related='company_id.work_from_office_ip_2',
        readonly=False
    )
