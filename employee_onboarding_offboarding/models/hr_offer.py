from email.policy import default
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HrOffer(models.Model):
    _name = "hr.offer"
    _description = "Employee Offer Creation"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    # Candidate Details
    candidate_name = fields.Char("Candidate Name", required=True, tracking=True)
    contact_number = fields.Char("Contact Number", required=True, tracking=True)
    personal_email = fields.Char("Personal Email", required=True, tracking=True)
    joining_date = fields.Date("Joining Date", required=True, tracking=True)
    job_id = fields.Many2one("hr.job", string="Designation", required=True, tracking=True)
    salary = fields.Float("Salary", tracking=True)
    allowances = fields.Float("Allowances", tracking=True)
    employment_type = fields.Selection([
        ("permanent", "Permanent"),
        ("contract", "Contract"),
        ("intern", "Internship"),
    ], string="Employment Type", required=True, tracking=True)
    probation_period = fields.Integer("Probation Period (months)", default=3, tracking=True)

    # Client Assignment
    client_id = fields.Many2one("res.partner", string="Client", required=True, domain="[('is_company','=',True)]", tracking=True)
    client_joining_date = fields.Date("Client Joining Date", tracking=True)
    pillar = fields.Selection([
        ("business", "Business"),
        ("tech", "Tech"),
    ], string="Business/Tech Pillar", required=True, tracking=True)
    work_location = fields.Selection([
        ("onsite", "On-Site"),
        ("remote", "Remote"),
        ("hybrid", "Hybrid"),
    ], string="Work Location",default='onsite', required=True, tracking=True)
    reporting_time = fields.Char("Reporting Time", tracking=True)
    working_hours = fields.Float("Working Hours (per day)", tracking=True)

    # Reporting Structure
    manager_id = fields.Many2one("hr.employee", string="Internal Manager", required=True, tracking=True)
    manager = fields.Char(string='Manager (Client)')
    manager_email = fields.Char(string='Manager Email')
    dept_hod = fields.Char(string="Dept HOD", tracking=True)
    dept_hod_email = fields.Char(string="HOD Email", readonly=True, tracking=True)

    # Additional Notes
    buddy_info = fields.Char("Buddy Info", tracking=True)
    remarks = fields.Text("Modification Remarks", tracking=True)
    special_instructions = fields.Text("Special Instructions", tracking=True)
    offer_submitter_id = fields.Many2one('res.users', string='Offer Submitter')

    # Workflow
    state = fields.Selection([
        ("draft", "New"),
        ("submitted", "CEO Approval"),
        ("modification", "Modification"),
        ("approved", "Approved & Sent Offer"),
        ("send_employee_form", "Employee Form Sent"),
        ("send_contract", "Contract Sent"),
        ("rejected", "Rejected"),
    ], default="draft", tracking=True)

    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, '%s - ( %s)' % (rec.candidate_name, rec.client_id.name)))
        return result

    # System Validation
    @api.constrains("candidate_name", "contact_number", "personal_email",
                    "joining_date", "job_id", "salary", "employment_type",
                    "client_id", "client_joining_date", "pillar", "work_location",
                    "reporting_time", "working_hours", "manager_id", "dept_hod")
    def _check_required_fields(self):
        for rec in self:
            mandatory_fields = [
                rec.candidate_name, rec.contact_number, rec.personal_email,
                rec.joining_date, rec.job_id, rec.salary, rec.employment_type,
                rec.client_id, rec.client_joining_date, rec.pillar, rec.work_location,
                rec.reporting_time, rec.working_hours, rec.manager_id, rec.dept_hod,
            ]
            if not all(mandatory_fields):
                raise ValidationError("All mandatory fields must be completed before submission.")

    # Workflow Actions
    def action_submit(self):
        self.write({
            "state": "submitted",
            "offer_submitter_id":self.env.user.id
        })

        # Get CEO group users
        ceo_group = self.env.ref("employee_onboarding_offboarding.group_ceo")
        ceo_users = ceo_group.users

        if not ceo_users:
            return

        # Get mail template
        template = self.env.ref("employee_onboarding_offboarding.candidate_offer_approval_template")

        if template:
            for user in ceo_users:
                # Send mail to each CEO
                template.send_mail(self.id, force_send=True, email_values={"email_to": user.email})

    def action_send_back(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "hr.offer.sendback.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"active_id": self.id},
        }

    def action_approve(self):
        if not self.env.user.has_group("employee_onboarding_offboarding.group_ceo"):
            raise ValidationError("Only CEO can approve offers.")

        self.write({"state": "approved"})

        # Send offer email to candidate
        template = self.env.ref("employee_onboarding_offboarding.candidate_offer_final_template")
        if template and self.personal_email:
            template.send_mail(self.id, force_send=True)

    def action_reject(self):
        self.write({"state": "rejected"})
