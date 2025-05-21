from odoo import models, fields

class SurveyUserInput(models.Model):
    _inherit = 'survey.user_input'

    employee_id = fields.Many2one('hr.employee', string='Employee')
