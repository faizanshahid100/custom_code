from odoo import fields, models

class HrEmployeeExt(models.Model):
    _inherit = 'hr.employee'

    gazetted_holiday_id = fields.Many2one('gazetted.holiday', string='Gazetted Holiday Policy')
