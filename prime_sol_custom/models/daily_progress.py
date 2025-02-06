import logging
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError
from datetime import date


_logger = logging.getLogger(__name__)


class DailyProgress(models.Model):
    _name = "daily.progress"
    _inherit = "mail.thread"
    _description = "Daily Progress"
    _rec_name = 'resource_user_id'

    resource_user_id = fields.Many2one('res.users', string='Resource Name *', default=lambda self: self.env.user.id)
    date_of_project = fields.Date("Today Date", required=True, default=lambda self: date.today())
    is_admin = fields.Boolean(string='Is Admin', compute='_compute_is_admin')
    ticket_assigned_new = fields.Integer(string='Tasks / Tickets Assigned')
    avg_resolved_ticket = fields.Integer(string='Tasks / Tickets Resolved')
    avg_resolution_time = fields.Integer(string='Avg. Resolution Time (min.)')
    csat_new = fields.Float(string='CSAT %')
    billable_hours = fields.Float(string='Billable Hours %')
    no_calls_duration = fields.Integer(string='Number of Calls Attended')

    # for required fields or not
    # is_required_ticket_assigned_new = fields.Boolean('Is Tasks / Tickets Assigned Required?')
    is_required_avg_resolved_ticket = fields.Boolean('Is Tasks / Tickets Resolved Required?')
    # is_required_avg_resolution_time = fields.Boolean('Is Avg. Resolution Time (min.) Required?')
    # is_required_csat_new = fields.Boolean('Is CSAT % Required?')
    is_required_billable_hours = fields.Boolean('Is Billable Hours % Required?')
    is_required_no_calls_duration = fields.Boolean('Is Number of Calls Attended Required?')

    @api.model
    def create(self, vals):
        record = super(DailyProgress, self).create(vals)
        if record.resource_user_id:
            employee = record.resource_user_id.employee_id
            if not employee:
                return record

            # Define fields to check, excluding fields if their respective "is_required" flag is checked
            fields_to_check = {
                'avg_resolved_ticket': employee.d_ticket_resolved if not record.is_required_avg_resolved_ticket else None,
                'avg_resolution_time': employee.d_avg_resolution_time,
                'csat_new': employee.d_CAST,
                'billable_hours': employee.d_billable_hours if not record.is_required_billable_hours else None,
                'no_calls_duration': employee.d_no_of_call_attended if not record.is_required_no_calls_duration else None,
            }

            field_metadata = self.fields_get()

            # Identify missing fields
            missing_fields = [
                field_metadata[field_name]['string']
                for field_name, value in fields_to_check.items()
                if value and not record[field_name]
            ]

            # Raise error if any required fields are missing
            if missing_fields:
                raise ValidationError("The following fields are mandatory. Please fill:\n" + "\n".join(missing_fields))

        return record

    def write(self, vals):
        res = super(DailyProgress, self).write(vals)
        for record in self:
            user_id = vals.get('resource_user_id') or record.resource_user_id
            if user_id:
                employee = user_id.employee_id
                if employee:
                    # Define fields to check, excluding fields if their respective "is_required" flag is checked
                    fields_to_check = {
                        'avg_resolved_ticket': employee.d_ticket_resolved if not record.is_required_avg_resolved_ticket else None,
                        'avg_resolution_time': employee.d_avg_resolution_time,
                        'csat_new': employee.d_CAST,
                        'billable_hours': employee.d_billable_hours if not record.is_required_billable_hours else None,
                        'no_calls_duration': employee.d_no_of_call_attended if not record.is_required_no_calls_duration else None,
                    }

                    field_metadata = self.fields_get()

                    # Identify missing fields
                    missing_fields = [
                        field_metadata[field_name]['string']
                        for field_name, value in fields_to_check.items()
                        if value and not record[field_name]
                    ]

                    # Raise error if any required fields are missing
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