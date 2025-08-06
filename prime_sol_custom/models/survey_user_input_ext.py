from odoo import models, fields, api
from dateutil import parser

class SurveyUserInput(models.Model):
    _inherit = 'survey.user_input'

    employee_id = fields.Many2one('hr.employee', string='Employee')
    partner_id = fields.Many2one('res.partner','Client', related='employee_id.contractor')
    response_date = fields.Date('Client Response Date', compute='_compute_response_date', store=True)

    @api.depends('employee_id', 'user_input_line_ids.question_id', 'user_input_line_ids.display_name')
    def _compute_response_date(self):
        for rec in self:
            # Filter for the line where question is "Date"
            date_line = rec.user_input_line_ids.filtered(lambda l: l.answer_type == 'date')
            if date_line:
                try:
                    # Try to parse the display_name as a date
                    parsed_date = parser.parse(date_line[0].display_name)
                    rec.response_date = parsed_date.date()
                except Exception:
                    rec.response_date = False
            else:
                rec.response_date = False