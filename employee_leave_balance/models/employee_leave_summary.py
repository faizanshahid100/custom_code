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

    def generate_leave_summary(self):
        self.search([]).unlink()
        current_year = date.today().year

        employees = self.env["hr.employee"].search([("active", "=", True)])

        for emp in employees:
            taken = {}
            assigned = {}

            # --- Leaves Taken ---
            leaves = self.env["hr.leave"].search([
                ("employee_id", "=", emp.id),
                ("state", "=", "validate"),
                ("request_date_from", ">=", f"{current_year}-01-01"),
                ("request_date_to", "<=", f"{current_year}-12-31"),
            ])

            for l in leaves:
                key = l.holiday_status_id.name.lower()
                taken[key] = round(taken.get(key, 0.0) + l.number_of_days_display, 2)

            # --- Leaves Assigned ---
            allocations = self.env["hr.leave.allocation"].search([
                ("employee_id", "=", emp.id),
                ("state", "=", "validate"),
            ])

            for a in allocations:
                key = a.holiday_status_id.name.lower()
                assigned[key] = round(assigned.get(key, 0.0) + a.number_of_days_display, 2)

            def val(name):
                return f"{taken.get(name, 0.0)} / {assigned.get(name, 0.0)}"

            total = round(sum(assigned.values()), 2)
            used = round(sum(taken.values()), 2)
            remaining = round(total - used, 2)

            self.create({
                "employee_id": emp.id,
                "floater": val("floater leaves"),
                "sick": val("sick leaves"),
                "unpaid": val("unpaid"),
                "parental": val("parental leaves"),
                "annual": val("annual leaves"),
                "public": val("public time-off"),
                "compensatory": val("compensatory leaves"),
                "total": str(total),
                "used": str(used),
                "remaining": str(remaining),
            })
