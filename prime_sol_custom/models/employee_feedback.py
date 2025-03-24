from odoo import models, fields, api, _

class EmployeeFeedback(models.Model):
    _name = 'hr.employee.feedback'
    _rec_name = 'employee_id'
    _description = 'Employee Feedback'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, readonly=False)
    date_feedback = fields.Date(string='Date', required=True)
    client_id = fields.Many2one('res.partner', string='Client Name', required=True, domain=[('is_company','=', True)])
    client_feedback = fields.Text('Client Feedback', required=True)
    feedback_type = fields.Selection([
        ('positive', 'Positive'),
        ('negative', 'Negative')
    ], string='Feedback Type', required=True)
    outcome_suggested = fields.Text(string='Outcome Suggested', required=True)
    next_followup_date = fields.Date(string='Next Follow-up')
