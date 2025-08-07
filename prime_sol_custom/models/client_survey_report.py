from datetime import date, timedelta
from odoo import api, fields, models
from odoo.exceptions import ValidationError

class ClientSurveyReport(models.Model):
    _name = "client.survey.report"
    _description = 'Client Survey Report'

    response_date = fields.Date('Response Date')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    partner_id = fields.Many2one('res.partner', string='Client')
    client_manager = fields.Char(string='Manager (Client)')
    level = fields.Char('Level')
    avg_points = fields.Float('Avg. points')

