from odoo import models, fields, api

class EmployeePulseProfile(models.Model):
    _name = 'employee.pulse.profile'
    _rec_name = 'employee_id'
    _description = 'Employee Pulse Profile'

    employee_id = fields.Many2one('hr.employee', string="Employee Name", required=True, ondelete="cascade")
    comment = fields.Char('Comment')

    _0_1_probation_meeting_ids = fields.One2many(
        'employee.probation.meeting',
        'employee_pulse_id',
        string="0-1 Month Probation Meetings",
        domain=[('probation_time', '=', '0_1')]
    )
    _1_3_probation_meeting_ids = fields.One2many(
        'employee.probation.meeting',
        'employee_pulse_id',
        string="1-3 Month Probation Meetings",
        domain=[('probation_time', '=', '1_3')]
    )

    _3_6_probation_meeting_ids = fields.One2many(
        'employee.probation.meeting',
        'employee_pulse_id',
        string="3-6 Months Probation Meetings",
        domain=[('probation_time', '=', '3_6')]
    )
    _6_onwards_probation_meeting_ids = fields.One2many(
        'employee.probation.meeting',
        'employee_pulse_id',
        string="6 Onward Months Probation Meetings",
        domain=[('probation_time', '=', '6_onwards')]
    )

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
