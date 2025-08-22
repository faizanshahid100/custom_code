from email.policy import default

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HrOffer(models.Model):
    _name = "hr.offer"
    _description = "Employee Offer Creation"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    # Candidate Details
    candidate_name = fields.Char("Candidate Name", required=True)
    contact_number = fields.Char("Contact Number", required=True)
    personal_email = fields.Char("Personal Email", required=True)
    joining_date = fields.Date("Joining Date", required=True)
    designation = fields.Many2one("hr.job", string="Designation", required=True)
    salary = fields.Float("Salary", required=True)
    allowances = fields.Float("Allowances")
    employment_type = fields.Selection([
        ("permanent", "Permanent"),
        ("contract", "Contract"),
        ("intern", "Internship"),
    ], string="Employment Type", required=True)
    probation_period = fields.Integer("Probation Period (months)", default=3)

    # Client Assignment
    client_id = fields.Many2one("res.partner", string="Client", required=True, domain="[('is_company','=',True)]")
    client_joining_date = fields.Date("Client Joining Date", required=True)
    pillar = fields.Selection([
        ("business", "Business"),
        ("tech", "Tech"),
    ], string="Business/Tech Pillar", required=True)
    work_location = fields.Selection([
        ("onsite", "On-Site"),
        ("remote", "Remote"),
        ("hybrid", "Hybrid"),
    ], string="Work Location",default='onsite', required=True)
    reporting_time = fields.Char("Reporting Time", required=True)
    working_hours = fields.Float("Working Hours (per day)", required=True)

    # Reporting Structure
    manager_id = fields.Many2one("hr.employee", string="Manager", required=True)
    hod_id = fields.Many2one("hr.employee", string="Head of Department", required=True)
    manager_email = fields.Char(related="manager_id.work_email", string="Manager Email", readonly=True)
    hod_email = fields.Char(related="hod_id.work_email", string="HOD Email", readonly=True)

    # Additional Notes
    buddy_info = fields.Char("Buddy Info")
    remarks = fields.Text("Remarks")
    special_instructions = fields.Text("Special Instructions")

    # Workflow
    state = fields.Selection([
        ("draft", "Draft"),
        ("submitted", "Submitted for CEO Approval"),
        ("modification", "Sent Back for Modification"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ], default="draft", tracking=True)

    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, '%s - ( %s)' % (rec.candidate_name, rec.client_id.name)))
        return result

    # System Validation
    @api.constrains("candidate_name", "contact_number", "personal_email",
                    "joining_date", "designation", "salary", "employment_type",
                    "client_id", "client_joining_date", "pillar", "work_location",
                    "reporting_time", "working_hours", "manager_id", "hod_id")
    def _check_required_fields(self):
        for rec in self:
            mandatory_fields = [
                rec.candidate_name, rec.contact_number, rec.personal_email,
                rec.joining_date, rec.designation, rec.salary, rec.employment_type,
                rec.client_id, rec.client_joining_date, rec.pillar, rec.work_location,
                rec.reporting_time, rec.working_hours, rec.manager_id, rec.hod_id,
            ]
            if not all(mandatory_fields):
                raise ValidationError("All mandatory fields must be completed before submission.")

    # Workflow Actions
    def action_submit(self):
        self.write({"state": "submitted"})

    def action_send_back(self):
        self.write({"state": "modification"})

    def action_approve(self):
        if not self.env.user.has_group("employee_onboarding_offboarding.group_ceo"):
            raise ValidationError("Only CEO can approve offers.")
        self.write({"state": "approved"})

    def action_reject(self):
        self.write({"state": "rejected"})
