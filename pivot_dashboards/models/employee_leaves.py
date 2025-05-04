from odoo import models, fields


class EmployeeLeaveDashboardLine(models.Model):
    _name = 'employee.leave.dashboard.line'
    _description = 'Employee Leave Dashboard Line'

    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    leave_type_id = fields.Many2one('hr.leave.type', string="Leave Type", required=True)

    total_assigned = fields.Float(string="Total Assigned Leaves")
    leaves_taken = fields.Float(string="Leaves Taken")
    leaves_remaining = fields.Float(string="Leaves Remaining")