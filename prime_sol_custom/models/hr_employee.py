from PIL.ImageChops import offset
from odoo import models, fields, api, _


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    hour_start_from = fields.Float('Hour Start From', default=0.0)
    total_working_hour = fields.Float('Total Working Hour', default=5.0)

    d_ticket_resolved = fields.Integer('Ticket Resolved')
    d_avg_resolution_time = fields.Integer('Avg.Resolution Time')
    d_CAST = fields.Integer('CAST %')
    d_billable_hours = fields.Integer('Billable Hours%')
    d_no_of_call_attended = fields.Integer('No Of Call Attended')

    ticket_resolved = fields.Integer('Ticket Resolved')
    avg_resolution_time = fields.Integer('Avg.Resolution Time')
    CAST = fields.Integer('CAST %')
    billable_hours = fields.Integer('Billable Hours')

    dayofweek = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
    ], 'Day of Week', compute="_compute_working_days")

    feedback_ids = fields.One2many('hr.employee.feedback', 'employee_id', string='Feedback')
    # Computed fields for feedback counts
    positive_feedback_count = fields.Integer(string="Positive Feedback", compute="_compute_feedback_counts")
    negative_feedback_count = fields.Integer(string="Negative Feedback", compute="_compute_feedback_counts")
    total_feedback_count = fields.Integer(string="Total Feedback", compute="_compute_feedback_counts")

    @api.depends('feedback_ids.feedback_type')
    def _compute_feedback_counts(self):
        for employee in self:
            employee.positive_feedback_count = sum(
                1 for feedback in employee.feedback_ids if feedback.feedback_type == 'positive')
            employee.negative_feedback_count = sum(
                1 for feedback in employee.feedback_ids if feedback.feedback_type == 'negative')

            employee.total_feedback_count = employee.positive_feedback_count + employee.negative_feedback_count


    # Action to open feedback records
    def action_view_positive_feedback(self):
        return {
            'name': 'Employee Feedback',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'hr.employee.feedback',
            'domain': [('employee_id', '=', self.id), ('feedback_type', '=', 'positive')],  # Filter only positive feedback
            'context': {'default_employee_id': self.id},
        }
    def action_view_negative_feedback(self):
        return {
            'name': 'Employee Feedback',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'hr.employee.feedback',
            'domain': [('employee_id', '=', self.id), ('feedback_type', '=', 'negative')],  # Filter only negative feedback
            'context': {'default_employee_id': self.id},
        }
    def action_view_feedback(self):
        return {
            'name': 'Employee Feedback',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'hr.employee.feedback',
            'domain': [('employee_id', '=', self.id)],
            # Filter all feedback
            'context': {'default_employee_id': self.id},
        }