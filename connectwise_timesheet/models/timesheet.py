from odoo import models, fields

class ConnectwiseTimesheet(models.Model):
    _name = 'connectwise.timesheet'
    _rec_name = 'employee_id'
    _description = 'ConnectWise Daily Timesheet'
    _order = 'work_date desc'

    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        default=lambda self: self.env.user.employee_id
    )

    work_date = fields.Date(string='Date', required=True)
    total_hours = fields.Float(string='Total Working Hours')

    line_ids = fields.One2many(
        'connectwise.timesheet.line',
        'timesheet_id',
        string='Timesheet Lines'
    )


class ConnectwiseTimesheetLine(models.Model):
    _name = 'connectwise.timesheet.line'
    _description = 'ConnectWise Timesheet Line'

    timesheet_id = fields.Many2one(
        'connectwise.timesheet',
        string='Timesheet',
        ondelete='cascade',
        required=True
    )

    timespan = fields.Char(string='Time Span')
    charge_to = fields.Char(string='Charge To')
    work_role = fields.Char(string='Work Role')
    actual_hours = fields.Float(string='Actual Hours')
    notes = fields.Text(string='Notes')
