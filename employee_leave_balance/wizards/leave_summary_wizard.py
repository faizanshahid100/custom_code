from odoo import models, fields
from datetime import date


class LeaveSummaryWizard(models.TransientModel):
    _name = "leave.summary.wizard"
    _description = "Leave Summary Wizard"

    date_from = fields.Date(
        string="Start Date",
        required=True,
        default=lambda self: date.today().replace(month=1, day=1)
    )
    date_to = fields.Date(
        string="End Date",
        required=True,
        default=lambda self: date.today()
    )

    def action_generate_report(self):
        current_year = date.today().year

        summary_model = self.env["employee.leave.summary"]
        summary_model.search([]).unlink()
        employees = self.env["hr.employee"].search([("active", "=", True)])

        for emp in employees:
            taken = {}
            assigned = {}

            # --- Leaves Taken ---
            leaves = self.env["hr.leave"].search([
                ("employee_id", "=", emp.id),
                ("state", "=", "validate"),
                ("request_date_from", ">=", self.date_from),
                ("request_date_to", "<=", self.date_to),
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

            summary_model.sudo().create({
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
        return {
            "type": "ir.actions.act_window",
            "name": "Employee Leave Summary",
            "res_model": "employee.leave.summary",
            "view_mode": "tree",
            "target": "current",
        }