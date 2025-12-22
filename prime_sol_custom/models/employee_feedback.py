from odoo import models, fields, api, _

class EmployeeFeedback(models.Model):
    _name = 'hr.employee.feedback'
    _rec_name = 'employee_id'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = 'Employee Feedback'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, readonly=False)
    date_feedback = fields.Date(string='Date', required=True)
    client_id = fields.Many2one('res.partner', string='Client Name', required=True, domain=[('is_company','=', True)])
    manager_id = fields.Many2one('res.partner', string='Manager')
    manager_email = fields.Char(string='Manager Email', compute='_compute_manager_fields', store=True, readonly=False)
    current_meeting_frequency = fields.Selection([
        ('monthly', 'Monthly'),
        ('bi_monthly', 'Bi-Monthly'),
        ('weekly', 'Weekly'),
        ('bi_weekly', 'Bi-Weekly'),
        ('tbd', 'TBD'),
        ('not_required', 'Not Required')
    ], string='Current Meeting Frequency', compute='_compute_manager_fields', store=True, readonly=False)
    business_tech = fields.Char(string='Business/Tech', compute='_compute_manager_fields', store=True, readonly=False)
    client_feedback = fields.Text('Client Feedback', required=True)
    month = fields.Date(string='Month')
    current_month_schedule = fields.Datetime(string='Current Month Schedule')
    feedback_type = fields.Selection([
        ('positive', 'Positive'),
        ('negative', 'Negative'),
        ('positive_neutral', 'Positive Neutral'),
        ('negative_neutral', 'Negative Neutral'),
    ], string='Feedback Type', required=True)
    gar = fields.Selection([
        ("green", "Green"),
        ("yellow", "Yellow"),
        ("red", "Red"),
    ], string="Employee Status", default='green', required=True, tracking=True)
    outcome_suggested = fields.Text(string='Outcome Suggested', required=True)
    next_followup_date = fields.Date(string='Next Follow-up')
    feedback_status = fields.Selection([
        ('casual', 'Casual'),
        ('inprogress', 'Inprogress'),
        ('resolved', 'Resolved'),
    ], string="Feedback Status", default='casual', required=True)
    comment = fields.Text()
    is_meeting_done = fields.Boolean(string='Is Meeting Done?')
    is_meeting_rescheduled = fields.Boolean(string='Is Meeting Rescheduled?')


    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        """ Set client_id to the contractor of the selected employee """
        if self.employee_id and self.employee_id.contractor:
            self.client_id = self.employee_id.contractor
        else:
            self.client_id = False  # Clear the field if no contractor is found

    @api.depends('manager_id.email', 'manager_id.business_tech', 'manager_id.current_meeting_frequency')
    def _compute_manager_fields(self):
        """Compute all dependent manager-related fields."""
        for record in self:
            manager = record.manager_id
            record.manager_email = manager.email or False
            record.business_tech = manager.business_tech or False
            record.current_meeting_frequency = manager.current_meeting_frequency or False