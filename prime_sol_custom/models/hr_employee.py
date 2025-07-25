from PIL.ImageChops import offset
from odoo import models, fields, api, _
from datetime import datetime, timedelta


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    hour_start_from = fields.Float('Hour Start From', default=0.0)
    total_working_hour = fields.Float('Total Working Hour', default=9.0)

    kpi_measurement = fields.Selection([('na', 'N/A' ), ('billable', 'Billable'), ('kpi', 'KPI')], default='na', required=1)
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
            'domain': [('employee_id', '=', self.id), ('feedback_type', '=', 'positive')],
            # Filter only positive feedback
            'context': {'default_employee_id': self.id},
        }

    def action_view_negative_feedback(self):
        return {
            'name': 'Employee Feedback',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'hr.employee.feedback',
            'domain': [('employee_id', '=', self.id), ('feedback_type', '=', 'negative')],
            # Filter only negative feedback
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

    @api.model
    def send_birthday_reminders(self):
        today = datetime.today().date()
        employees = self.search([('birthday', '!=', False)])
        channel = self.env['mail.channel'].search([('name', '=', 'People & Culture')], limit=1)

        if not channel:
            return  # No channel found

        for employee in employees:
            birthday = employee.birthday
            if not birthday:
                continue

            birthday_this_year = birthday.replace(year=today.year)

            if birthday_this_year < today:
                birthday_this_year = birthday_this_year.replace(year=today.year + 1)

            days_until = (birthday_this_year - today).days

            if 0 <= days_until <= 3:
                if days_until == 0:
                    msg = (
                        f"<b>🎉 It's {employee.name}'s Birthday Today! 🎂</b><br/>"
                        f"Let's celebrate and send your best wishes! 🥳<br/><br/><br/>"
                    )
                else:
                    msg = (
                        f"<b>🎉 Upcoming Birthday Alert! 🎉</b><br/>"
                        f"{employee.name}'s birthday is on <b>{birthday_this_year.strftime('%d %B')}</b> "
                        f"(<i>{days_until} day{'s' if days_until != 1 else ''} left</i>).<br/><br/><br/>"
                    )
                channel.message_post(
                    body=msg,
                    message_type='comment',
                    subtype_xmlid='mail.mt_note',
                )
