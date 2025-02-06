import logging
from odoo import api, fields, models
from datetime import timedelta
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class WeeklyProgress(models.Model):
    _name = "weekly.progress"
    _inherit = "mail.thread"
    _description = "Weekly Progress"

    date_of_project = fields.Date("Date *", required=True)
    name = fields.Char(string='Resource Name')
    formatted_date = fields.Char("Week Number", compute='_compute_formatted_date', store=True)

    resource_name = fields.Char(string='Resource Name *', compute='_compute_resource_name', readonly=False, store=True,)
    resource_user_id = fields.Many2one('res.users', string='Resource Name *', default=lambda self: self.env.user.id,)
    is_admin = fields.Boolean(string='Is Admin', compute='_compute_is_admin')
    display_name = fields.Char(string='Resource Name', compute='_compute_display_name', store=True)

    @api.model
    def _cron_check_weekly_progress(self):
        today = fields.Date.context_today(self)
        start_of_week = today - timedelta(days=today.weekday())

        start_of_previous_week = start_of_week - timedelta(weeks=1)
        end_of_previous_week = start_of_previous_week + timedelta(days=6)

        users = self.env['res.users'].search([('active', '=', True), ('employee_id.department_id.name', '=', 'MSP Pakistan')])

        users_without_progress = []
        for user in users:
            progress_records = self.env['weekly.progress'].search([('resource_user_id', '=', user.id),
                ('date_of_project', '>=', start_of_previous_week),
                ('date_of_project', '<=', end_of_previous_week)])
            if not progress_records:
                users_without_progress.append(user)

        for user in users_without_progress:
            if user:
                try:
                    template = self.env.ref('prime_sol_custom.email_template_weekly_progress_reminder')
                    template.send_mail(user.id, force_send=True)
                except ValueError as e:
                    _logger.error(f"Failed to send email to user {user.id}: {e}")
                except Exception as e:
                    _logger.error(f"Unexpected error occurred: {e}")

    @api.depends('resource_name', 'resource_user_id')
    def _compute_display_name(self):
        for record in self:
            record.display_name = record.resource_name if record.resource_name else record.resource_user_id.name


    @api.depends('resource_user_id')
    def _compute_resource_name(self):
        for record in self:
            if not record.is_admin:
                record.resource_name = record.resource_user_id.name

    @api.depends('resource_user_id')
    def _compute_is_admin(self):
        for record in self:
            record.is_admin = self.env.user.has_group('base.group_system')



    @api.depends('date_of_project')
    def _compute_formatted_date(self):
        for record in self:
            if record.date_of_project:
                date_obj = fields.Date.from_string(record.date_of_project)
                year = date_obj.year % 100  # Last two digits of the year
                week_number = date_obj.isocalendar()[1]  # Week number of the year
                record.formatted_date = f"{year:02d}-W{week_number:02d}"
            else:
                record.formatted_date = ""

    ticket_assigned_new = fields.Integer(string='Tasks / Tickets Assigned')
    avg_resolution_backlogs = fields.Integer(string='Tasks / Tickets Backlogs')
    avg_resolution_time = fields.Integer(string='Avg. Resolution Time (min.)')
    avg_resolution_datetime = fields.Datetime(string='Avg Resolution Time (as datetime)',
                                              compute='_compute_avg_resolution_datetime')
    avg_resolved_ticket = fields.Integer(string='Tasks / Tickets Resolved')
    csat_new = fields.Float(string='CSAT %')
    billable_hours = fields.Float(string='Billable Hours %')
    no_calls_duration = fields.Integer(string='Number of Calls Attended')


    @api.constrains('csat_new', 'avg_resolution_time', 'ticket_assigned_new', 'avg_resolved_ticket', 'billable_hours')
    def _check_values(self):
        for record in self:
            if record.csat_new < 0:
                raise ValidationError('CSAT % must be a positive number.')
            if not (0 <= record.csat_new <= 100):
                raise ValidationError('CSAT % must be between 0 and 100.')
            if len(str(record.csat_new).split('.')[1]) > 2:
                raise ValidationError('CSAT % must have up to two decimal places.')
            if record.avg_resolution_time < 0:
                raise ValidationError('Avg. Resolution Time (min.) must be a positive number.')
            if record.ticket_assigned_new < 0:
                raise ValidationError('Tasks / Tickets Assigned must be a positive number.')
            if record.avg_resolved_ticket < 0:
                raise ValidationError('Tasks / Tickets Resolved must be a positive number.')
            if record.billable_hours < 0:
                raise ValidationError('Billable Hours % must be a positive number.')
            if not (0 <= record.billable_hours <= 100):
                raise ValidationError('Billable Hours % must be between 0 and 100.')
            if len(str(record.billable_hours).split('.')[1]) > 2:
                raise ValidationError('Billable Hours % must have up to two decimal places.')