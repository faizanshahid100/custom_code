from email.policy import default

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class MeetingTracker(models.Model):
    _name = "meeting.tracker"
    _rec_name = "client_id"
    _description = "Meeting Tracker"

    date = fields.Date(string="Date", required=True, default=fields.Date.today)
    record_person = fields.Many2one('hr.employee', string="Record Person", default=lambda self: self.env.user.employee_id, readonly=True)
    client_id = fields.Many2one('res.partner', required=True, string="Client", domain=[('is_company','=', True)])
    kpi_measurement = fields.Selection([('na', 'N/A'), ('billable', 'Billable'), ('kpi', 'KPI')], default='kpi')
    department_id = fields.Many2one('hr.department', string='Department')
    meeting_type = fields.Selection([
        ('internal', 'Internal Online'),
        ('onsite', 'Onsite Engagement Events'),
    ], string="Meeting Type", default='internal')
    state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed')], string="Status", default="draft")
    meeting_details = fields.One2many('meeting.details', 'meeting_id', string="Meeting Details")

    def name_get(self):
        """ Returns a custom name combining Client and Date """
        result = []
        for record in self:
            name = f"{record.client_id.name} ({record.date})" if record.client_id and record.date else record.client_id.name or "Meeting"
            result.append((record.id, name))
        return result

    def action_confirm(self):
        """ Confirms the meeting tracker, preventing further edits """
        self.write({'state': 'confirmed'})

    def action_draft(self):
        """ Revert back to Draft """
        self.write({'state': 'draft'})

    @api.model
    def create(self, vals):
        """ Automatically create meeting details for all active employees when a Meeting Tracker record is created. """
        meeting = super(MeetingTracker, self).create(vals)
        meeting._auto_create_meeting_details(vals.get('client_id'))
        return meeting

    def write(self, vals):
        """ Also trigger meeting details creation when client_id is updated. """
        res = super(MeetingTracker, self).write(vals)
        if 'client_id' in vals:
            # 🔴 Delete existing meeting details before adding new ones
            self.meeting_details.unlink()
            self._auto_create_meeting_details(vals.get('client_id'))
        return res

    def _auto_create_meeting_details(self, client_id):
        """ Helper function to create meeting details for active employees of the selected client. """
        if not client_id:
            return

        for meeting in self:
            employees = self.env['hr.employee'].search([
                ('active', '=', True),
                ('contractor', '!=', False),
                ('contractor', '=', client_id),
            ])

            meeting_details = []
            for employee in employees:
                meeting_details.append({
                    'meeting_id': meeting.id,
                    'employee_id': employee.id,
                    'client_id': employee.contractor.id if employee.contractor else False,
                    'meeting_start_date': fields.Datetime.now(),
                    'meeting_end_date': fields.Datetime.now(),
                    'is_present': True,  # Default to Present
                })

            if meeting_details:
                self.env['meeting.details'].create(meeting_details)


class MeetingDetails(models.Model):
    _name = "meeting.details"
    _rec_name = "employee_id"
    _description = "Meeting Details"

    meeting_id = fields.Many2one('meeting.tracker', string="Meeting Tracker", ondelete="cascade")
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    client_id = fields.Many2one('res.partner', string="Client", domain=[('is_company','=', True)])
    project = fields.Char(string='Project')
    meeting_start_date = fields.Datetime(string="Meeting Start Date", required=True)
    meeting_end_date = fields.Datetime(string="Meeting End Date", required=True)
    meeting_duration = fields.Float(
        string="Duration (Hours)",
        compute="_compute_meeting_duration",
        store=True
    )
    is_present = fields.Boolean(string='Is Present', default=True)

    @api.depends('meeting_start_date', 'meeting_end_date')
    def _compute_meeting_duration(self):
        for record in self:
            if record.meeting_start_date and record.meeting_end_date:
                duration = (record.meeting_end_date - record.meeting_start_date).total_seconds() / 3600.0
                record.meeting_duration = max(duration, 0)
            else:
                record.meeting_duration = 0

    @api.constrains('meeting_start_date', 'meeting_end_date')
    def _check_meeting_dates(self):
        for record in self:
            if record.meeting_start_date and record.meeting_end_date:
                if record.meeting_start_date > record.meeting_end_date:
                    raise ValidationError(_("Meeting start date cannot be after the end date."))

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        """Sets default client_id from employee's contractor"""
        if self.employee_id and self.employee_id.contractor:
            self.client_id = self.employee_id.contractor