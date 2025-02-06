from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date, datetime, timedelta


class LeaveAttendance(models.Model):
    _name = "leave.attendance"
    _rec_name = "employee_id"
    _description = "Attendance approvals"
    _inherit = 'mail.thread'

    employee_id = fields.Many2one('hr.employee', string='Employee Name*', default=lambda self: self._get_default_employee())
    working_date = fields.Date('Working Date')
    check_in = fields.Datetime('Check-In time*')
    check_out = fields.Datetime('Check-Out time*')
    request_type = fields.Selection([('missing_attendance', 'Missing Attendance'), ('leave', 'Leave')], string="Request Type", default='missing_attendance')
    file = fields.Binary('Document')
    description = fields.Text('Description')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('approved', 'Approved'),
        ('reject', 'Rejected'),
    ], default='draft', string='Status', tracking=True)

    def _get_default_employee(self):
        # Get the current user's employee record
        employee = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
        return employee or False

    @api.constrains('check_in', 'check_out')
    def _check_check_in_check_out(self):
        # Check if check_in is before check_out
        for record in self:
            if record.check_in and record.check_out:
                if record.check_in >= record.check_out:
                    raise ValidationError("Check-In time must be before Check-Out time.")

    def _create_attendance_entry(self):
        # To create Attendance of specific days from Approval Hierarchy
        self.env['hr.attendance'].create({
            'employee_id' : self.employee_id.id,
            'check_in' : self.check_in,
            'check_out' : self.check_out,
        })

    def action_confirm(self):
        # Transition from Draft to Confirmed
        self.state = 'confirmed'
        return True

    def action_approve(self):
        # Transition from Confirmed to Approved
        self.state = 'approved'
        # Create the attendance entry
        self._create_attendance_entry()

    def action_draft(self):
        # Transition from Reject to Draft
        self.state = 'draft'
        return True

    def action_reject(self):
        # Transition to Reject
        self.state = 'reject'
        return True