from odoo import models, fields


class EmployeeLeaveDashboardLine(models.Model):
    _name = 'employee.leave.dashboard.line'
    _description = 'Employee Leave Dashboard Line'
    # access_employee_leave_dashboard_line, access_employee_leave_dashboard_line, model_employee_leave_dashboard_line,, 1, 1, 1, 1

    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    leave_type_id = fields.Many2one('hr.leave.type', string="Leave Type", required=True)

    total_assigned = fields.Float(string="Total Assigned Leaves")
    leaves_taken = fields.Float(string="Leaves Taken")
    leaves_remaining = fields.Float(string="Leaves Remaining")