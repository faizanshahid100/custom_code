from email.policy import default
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
import base64
from odoo import models, fields, api
from docx import Document
import os
from datetime import date


class HrOffer(models.Model):
    _name = "hr.offer"
    _description = "Employee Offer Creation"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    # Candidate Details
    candidate_name = fields.Char("Candidate Name", required=True, tracking=True)
    # contact_number = fields.Char("Contact Number", required=True, tracking=True)
    personal_email = fields.Char("Personal Email", required=True, tracking=True)
    official_email = fields.Char("Official Email", tracking=True)
    gazetted_holiday_id = fields.Many2one('gazetted.holiday', string='Gazetted Holiday Policy', tracking=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', ondelete='cascade')
    country_id = fields.Many2one('res.country', string="Country", required=True, tracking=True)
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
        ("management", "Management"),
    ], string="Business/Tech Pillar", required=True, tracking=True)
    work_location = fields.Selection([
        ("onsite", "On-Site"),
        ("fully_remote", "Remote"),
        ("hybrid", "Hybrid"),
    ], string="Work Location",default='onsite', required=True, tracking=True)
    reporting_time = fields.Char("Reporting Time", default='12:00 PM - 9:00 PM (PST PK)', tracking=True)
    working_hours = fields.Float("Working Hours (per day)", default=9.0, tracking=True)
    checklist_template_id = fields.Many2one('checklist.template', string='Checklist Template', tracking=True)

    # Reporting Structure
    manager_id = fields.Many2one("hr.employee", string="Internal Manager", required=True, tracking=True)
    manager = fields.Char(string='Manager (Client)')
    manager_email = fields.Char(string='Manager Email')
    department_id = fields.Many2one('hr.department', string='Department')
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
        ("approved", "Approved"),
        ("send_offer", "Offer Sent"),
        ("send_contract", "Contract Sent"),
        ("hired", "Hired"),
        ("rejected", "Rejected"),
    ], default="draft", tracking=True)

    # Contract Info (Existing fields also be used here)
    date_of_birth = fields.Date(string='Date of Birth', tracking=True)
    address = fields.Char(string='Address', tracking=True)
    candidate_mobile = fields.Char(string='Candidate Mobile', tracking=True)
    id_number = fields.Char(string='ID number/Passport', tracking=True)
    tax_number = fields.Char(string='Tax ID (NTN, TIN)', tracking=True)
    ice_name = fields.Char(string='ICE Name', tracking=True)
    ice_number = fields.Char(string='ICE Number', tracking=True)
    ice_relation = fields.Char(string='ICE Relation', tracking=True)
    bank_name = fields.Char(string='Bank Name', tracking=True)
    bank_info = fields.Char(string='Branch City and Branch Code', tracking=True)
    account_number = fields.Char(string='Account Number', tracking=True)
    iban_number = fields.Char(string='IBAN Number', tracking=True)
    swift_code = fields.Char(string='SWIFT Code', tracking=True)
    linked_in_profile = fields.Char(string='LinkedIn Profile Link', tracking=True)


    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, '%s - ( %s)' % (rec.candidate_name, rec.client_id.name)))
        return result

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

    def action_sent_offer(self):
        if not self.env.user.has_group("employee_onboarding_offboarding.group_responsible_hr"):
            raise ValidationError("Only HR Responsible can Send offers.")

        self.write({"state": "send_offer"})

        # Send offer email to candidate
        template = self.env.ref("employee_onboarding_offboarding.candidate_offer_final_template")
        if template and self.personal_email:
            template.send_mail(self.id, force_send=True)

    def action_sent_contract(self):
        for record in self:
            record.write({"state": "send_contract"})

            # Get module base path
            module_path = os.path.dirname(os.path.abspath(__file__))
            base_path = os.path.join(module_path, "..")

            # Template in /data/
            template_path = os.path.join(base_path, "data", "contract_template.docx")

            # Contracts folder
            contracts_dir = os.path.join(base_path, "contracts")
            if not os.path.exists(contracts_dir):
                os.makedirs(contracts_dir)

            # Load template
            doc = Document(template_path)

            # Replace variables
            replacements = {
                "{{ candidate_name }}": record.candidate_name or "",
                "{{ id_number }}": record.id_number or "",
                "{{ address }}": record.address or "",
                "{{ offer_issue_date }}": fields.Date.today().strftime("%d %B %Y"),
                "{{ joining_date }}": record.joining_date.strftime("%d %B %Y") if record.joining_date else "",
                "{{ salary }}": str(record.salary) if record.salary else "",
                "{{ probation_period }}": str(record.probation_period or ""),
                "{{ work_location }}": record.work_location or "",
                "{{ reporting_time }}": record.reporting_time or "",
            }

            for para in doc.paragraphs:
                for key, value in replacements.items():
                    if key in para.text:
                        para.text = para.text.replace(key, value)

            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for key, value in replacements.items():
                            if key in cell.text:
                                cell.text = cell.text.replace(key, value)

            # Save final doc in contracts folder
            safe_name = record.candidate_name.replace(" ", "_")+'_'+record.id_number
            final_path = os.path.join(contracts_dir, f"Contract_{safe_name}.docx")
            doc.save(final_path)

            # Attach to Odoo
            with open(final_path, "rb") as f:
                file_data = f.read()

            attachment = self.env["ir.attachment"].create({
                "name": f"Contract_{safe_name}.docx",
                "type": "binary",
                "datas": base64.b64encode(file_data),
                "res_model": "hr.offer",
                "res_id": record.id,
                "mimetype": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            })

            # --- SEND EMAIL WITH ATTACHMENT ---
            mail_values = {
                "subject": "Independent Contractor Service Agreement",
                "body_html": f"""
                                <p>Dear <b>{record.candidate_name}</b>,</p>
                                <p>Please find attached your Independent Contractor Service Agreement.</p>
                                <p>Kindly review, sign, and reply back with confirmation.</p>
                                <br/>
                                <p><b>Regards,</b><br/>
                                HR Team<br/>
                                Prime System Solutions</p>
                            """,
                "email_from": "hr@primesystemsolutions.com",
                "email_to": record.personal_email,
                "email_cc": ','.join(user.email for user in record.env.ref('employee_onboarding_offboarding.group_responsible_hr').users if user.email),
                "attachment_ids": [(6, 0, [attachment.id])],
            }
            self.env["mail.mail"].sudo().create(mail_values).send()

    def action_hire(self):
        for record in self:
            # Change state
            record.write({"state": "hired"})

            # Validations
            if not record.official_email:
                raise ValidationError('Please enter Official Email first')
            elif not record.gazetted_holiday_id:
                raise ValidationError('Please enter Gazetted Holiday first')
            elif not record.checklist_template_id:
                raise ValidationError('Please enter Checklist first')

            user = self.env['res.users'].sudo().create({
                'name': record.candidate_name,
                'login': record.official_email,
                'password': '123',
            })

            # Create Employee
            employee_vals = {
                "name": record.candidate_name,
                "work_email": record.official_email,
                "work_phone": record.candidate_mobile,
                "mobile_phone": record.candidate_mobile,
                "private_email": record.personal_email,
                "birthday": record.date_of_birth,
                # "address_home_id": record.address_id.id if record.address_id else False,
                "job_id": record.job_id.id if record.job_id else False,
                "department_id": record.department_id.id if record.department_id else False,
                "parent_id": record.manager_id.id if record.manager_id else False,
                "coach_id": record.manager_id.id if record.manager_id else False,
                "country_id": record.country_id.id if record.country_id else False,
                # "bank_account_id": record.bank_account_id.id if hasattr(record, 'bank_account_id') else False,
                # "work_location_id": record.work_location_id.id if hasattr(record, 'work_location_id') else False,
                "manager": record.manager,
                "manager_email": record.manager_email,
                "dept_hod": record.dept_hod,
                "dept_hod_email": record.dept_hod_email,
                "joining_date": record.joining_date,
                "joining_salary": record.salary,
                "work_mode": record.work_location,
                "total_working_hour": record.working_hours,
                "gazetted_holiday_id": record.gazetted_holiday_id.id,
                "checklist_template_id": record.checklist_template_id.id,
                "emergency_contact": record.ice_name,
                "emergency_phone": record.ice_number,
                "emergency_contact_relation": record.ice_relation,
                "identification_id": record.id_number,
                "user_id": user.id,
            }

            employee = self.env["hr.employee"].sudo().create(employee_vals)

            # (Optional) link back offer → employee
            record.write({"employee_id": employee.id})

    def action_reject(self):
        self.write({"state": "rejected"})

    def request_official_email(self):
        for record in self:
            # Get IT Support users
            it_support_group = self.env.ref("employee_onboarding_offboarding.group_it_support")
            it_support_emails = [user.email for user in it_support_group.users if user.email]

            if not it_support_emails:
                raise UserError("No IT Support user with email found.")

            # Get HR Responsible users
            hr_group = self.env.ref("employee_onboarding_offboarding.group_responsible_hr")
            hr_emails = [user.email for user in hr_group.users if user.email]

            # Build subject & body
            subject = f"Request to Create Official Email - {record.candidate_name}"
            body = f"""
                Dear IT Support Team,<br/><br/>
                Please create an official email ID for the candidate <b>{record.candidate_name}</b>.<br/>
                Personal Email: {record.personal_email}<br/><br/>
                Once created, kindly inform HR Responsible ({', '.join(hr_emails)}).<br/><br/>
                Regards,<br/>
                HR Team
            """

            # Send mail
            mail_values = {
                "subject": subject,
                "body_html": body,
                "email_from": "hr@primesystemsolutions.com",
                "email_to": ",".join(it_support_emails),
                "email_cc": ",".join(hr_emails),
            }
            self.env["mail.mail"].sudo().create(mail_values).send()
