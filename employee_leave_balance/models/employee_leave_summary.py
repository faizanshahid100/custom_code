from odoo import models, fields, api
from datetime import date


class EmployeeLeaveSummary(models.Model):
    _name = "employee.leave.summary"
    _description = "Employee Leave Balance Summary"
    _auto = True

    employee_id = fields.Many2one("hr.employee", string="Employee")

    floater = fields.Char("Floater Leaves")
    sick = fields.Char("Sick Leaves")
    unpaid = fields.Char("Unpaid")
    parental = fields.Char("Parental Leaves")
    annual = fields.Char("Annual Leaves")
    public = fields.Char("Public Time-Off")
    compensatory = fields.Char("Compensatory Leaves")

    total = fields.Char("Total Leaves")
    used = fields.Char("Used Leaves")
    remaining = fields.Char("Remaining Leaves")
