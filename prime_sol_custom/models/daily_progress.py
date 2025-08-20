import math
import logging
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import date

_logger = logging.getLogger(__name__)


class DailyProgress(models.Model):
    _name = "daily.progress"
    _inherit = "mail.thread"
    _description = "Daily Progress"
    _rec_name = 'resource_user_id'

    resource_user_id = fields.Many2one('res.users', string='Resource Name *', default=lambda self: self.env.user.id)
    date_of_project = fields.Date("Today Date", required=True, default=lambda self: date.today())
    week_of_year = fields.Char(string="Week of the Year", compute="_compute_week_of_year", store=True)
    year_of_kpi = fields.Char(string="KPI Year")
    is_admin = fields.Boolean(string='Is Admin', compute='_compute_is_admin')
    ticket_assigned_new = fields.Integer(string='Tasks / Tickets Assigned')
    avg_resolved_ticket = fields.Integer(string='Tasks / Tickets Resolved')
    avg_resolution_time = fields.Integer(string='Avg. Resolution Time (min.)')
    csat_new = fields.Float(string='CSAT %')
    billable_hours = fields.Float(string='Billable Hours %')
    non_billable_hours = fields.Float(string='Non-Billable Hours %', compute='_compute_non_billable_hours', store=True)
    no_calls_duration = fields.Integer(string='Number of Calls Attended')
    # Daily Target
    daily_target_tickets_resolved = fields.Integer(related="resource_user_id.employee_id.d_ticket_resolved",
                                                   string="Daily Target Tickets Resolved")
    daily_target_billable_hours = fields.Integer(related="resource_user_id.employee_id.d_billable_hours",
                                                 string="Daily Target Billable Hours %")
    daily_target_call_attended = fields.Integer(related="resource_user_id.employee_id.d_no_of_call_attended",
                                                string="Daily Target Call Attended")

    # for required fields or not
    # is_required_ticket_assigned_new = fields.Boolean('Is Tasks / Tickets Assigned Required?')
    is_required_avg_resolved_ticket = fields.Boolean('No Ticket Resolved Today')
    # is_required_avg_resolution_time = fields.Boolean('Is Avg. Resolution Time (min.) Required?')
    # is_required_csat_new = fields.Boolean('Is CSAT % Required?')
    is_required_billable_hours = fields.Boolean('No Billable Hours Today')
    is_required_no_calls_duration = fields.Boolean('No Call Received Today')

    @api.constrains('date_of_project', 'resource_user_id')
    def _check_unique_date_and_user(self):
        """Ensure that no two records have the same date_of_project and resource_user_id."""
        for record in self:
            existing_record = self.env['daily.progress'].search([
                ('date_of_project', '=', record.date_of_project),
                ('resource_user_id', '=', record.resource_user_id.id),
                ('id', '!=', record.id)  # Exclude the current record in case of update
            ])
            if existing_record:
                raise ValidationError(
                    "A record with the same 'Today Date' and 'Resource Name' already exists. You cannot create duplicate records for the same user on the same date.")

    @api.model
    def create(self, vals):
        record = super(DailyProgress, self).create(vals)
        if record.resource_user_id:
            employee = record.resource_user_id.employee_id
            if not employee:
                return record

            # Only validate if the employee has a defined billable hours target
            if employee.d_billable_hours:
                total_hours = (record.billable_hours or 0) + (record.non_billable_hours or 0)
                if total_hours != 100:
                    raise ValidationError("The total of 'Billable Hours %' and 'Non-Billable Hours %' must be 100%.")

            # Fields to check if their respective "is_required" flags are not set
            fields_to_check = {
                'avg_resolved_ticket': employee.d_ticket_resolved if not record.is_required_avg_resolved_ticket else None,
                'billable_hours': employee.d_billable_hours if not record.is_required_billable_hours else None,
                'no_calls_duration': employee.d_no_of_call_attended if not record.is_required_no_calls_duration else None,
            }

            field_metadata = self.fields_get()
            missing_fields = [
                field_metadata[field_name]['string']
                for field_name, value in fields_to_check.items()
                if value and not record[field_name]
            ]

            if missing_fields:
                raise ValidationError("The following fields are mandatory. Please fill:\n" + "\n".join(missing_fields))

        return record

    def write(self, vals):
        res = super(DailyProgress, self).write(vals)
        for record in self:
            user_id = self.env['res.users'].browse(vals.get('resource_user_id')) or record.resource_user_id
            if user_id:
                employee = user_id.employee_id
                if employee:

                    # Recalculate billable + non-billable hours for validation
                    billable = vals.get('billable_hours', record.billable_hours)
                    non_billable = vals.get('non_billable_hours', record.non_billable_hours)

                    if employee.d_billable_hours:
                        total_hours = (billable or 0) + (non_billable or 0)
                        if total_hours != 100:
                            raise ValidationError(
                                "The total of 'Billable Hours %' and 'Non-Billable Hours %' must be 100%.")

                    fields_to_check = {
                        'avg_resolved_ticket': employee.d_ticket_resolved if not record.is_required_avg_resolved_ticket else None,
                        'billable_hours': employee.d_billable_hours if not record.is_required_billable_hours else None,
                        'no_calls_duration': employee.d_no_of_call_attended if not record.is_required_no_calls_duration else None,
                    }

                    field_metadata = self.fields_get()
                    missing_fields = [
                        field_metadata[field_name]['string']
                        for field_name, value in fields_to_check.items()
                        if value and not record[field_name]
                    ]

                    if missing_fields:
                        raise ValidationError(
                            "The following fields are mandatory. Please fill:\n" + "\n".join(missing_fields))

        return res

    @api.depends('resource_user_id')
    def _compute_is_admin(self):
        for record in self:
            record.is_admin = self.env.user.has_group('base.group_system')

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

    @api.onchange('date_of_project')
    def onchange_date_of_project(self):
        for rec in self:
            if rec.date_of_project and rec.date_of_project > date.today():
                raise UserError("The date of the project cannot be in the future. Please select a valid date.")

    @api.constrains('field1', 'field2', 'field3')
    def _check_mandatory_fields(self):
        for record in self:
            # Check if `user_id` is set
            if record.user_id:
                # If any of the fields have a value, make them all mandatory
                mandatory_fields = {
                    'field1': record.field1,
                    'field2': record.field2,
                    'field3': record.field3,
                }
                missing_fields = [field_name for field_name, value in mandatory_fields.items() if not value]
                if missing_fields:
                    raise ValidationError(
                        "The following fields are mandatory when a user is assigned: %s" % ", ".join(missing_fields)
                    )

    @api.depends('billable_hours')
    def _compute_non_billable_hours(self):
        for record in self:
            if 0 <= record.billable_hours <= 100:
                record.non_billable_hours = 100 - record.billable_hours
            else:
                record.non_billable_hours = 0  # You can handle invalid input as you wish

    @api.depends('date_of_project')
    def _compute_week_of_year(self):
        """Compute week number (ISO week) based on date_of_project."""
        for record in self:
            if record.date_of_project:
                # ISO week number (1–53, starting Monday)
                iso_year, week_number, _ = record.date_of_project.isocalendar()
                record.week_of_year = f"Week-{week_number}"
                record.year_of_kpi = iso_year
            else:
                record.week_of_year = ""
                record.year_of_kpi = ""
