from odoo import models, fields, api

class EmployeePulseProfile(models.Model):
    _name = 'employee.pulse.profile'
    _rec_name = 'employee_id'
    _description = 'Employee Pulse Profile'

    employee_id = fields.Many2one('hr.employee', string="Employee Name", required=True, ondelete="cascade")
    comment = fields.Char('Comment')

    pre_probation_meeting_ids = fields.One2many(
        'employee.probation.meeting',
        'employee_pulse_id',
        string="Pre-Probation Meetings",
        domain=[('probation_type', '=', 'pre')]
    )

    post_probation_meeting_ids = fields.One2many(
        'employee.probation.meeting',
        'employee_pulse_id',
        string="Post-Probation Meetings",
        domain=[('probation_type', '=', 'post')]
    )
