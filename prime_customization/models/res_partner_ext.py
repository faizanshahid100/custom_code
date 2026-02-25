from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    designation = fields.Selection(
        [('director', 'Director'),
        ('ceo', 'CEO'),
         ('president', 'President'),
         ('coo', 'COO'),
         ('chro', 'CHRO'),
         ('ta_team', 'TA Team'),
         ('hr_team', 'HR Team'),
         ('hr', 'HR')], string='Designation')

    def action_generate_members_report(self):
        return self.env['members.excel.report'].generate_excel_report()
