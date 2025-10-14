from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import date


class EmployeeProbationMeeting(models.Model):
    _name = "employee.probation.meeting"
    _description = "Employee Probation Meeting"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "employee_id"

    employee_id = fields.Many2one("hr.employee", string="Employee", required=True)
    date_meeting = fields.Date(string="Meeting Date", default=lambda self: date.today(), required=True)
    probation_type = fields.Selection([
        ("pre", "Pre-Probation"),
        ("post", "Post-Probation"),
    ], string="Probation Type", default='pre', required=True)

    meeting_status = fields.Selection([
        ("green", "Green"),
        ("yellow", "Yellow"),
        ("red", "Red"),
    ], string="Meeting Status", required=True, tracking=True)

    reason = fields.Text(string="Reason (If Yellow/Red)", help="Specify reason for concern if status is not Green", tracking=True)
    assignee_id = fields.Many2one('hr.employee', string='Task Assign To', tracking=True)

    # Questions
    q1_rating = fields.Selection([
        ('satisfied', 'Satisfied'),
        ('neutral', 'Neutral'),
        ('not_satisfied', 'Not Satisfied'),
    ], string="1. How is your experience going so far?")
    q1_experience = fields.Char(string="Q1 Explanation")

    q2_rating = fields.Selection([
        ('satisfied', 'Satisfied'),
        ('neutral', 'Neutral'),
        ('not_satisfied', 'Not Satisfied'),
    ], string="2. Are you aligned with the client?")
    q2_alignment = fields.Char(string="Q2 Explanation")

    q3_rating = fields.Selection([
        ('satisfied', 'Satisfied'),
        ('neutral', 'Neutral'),
        ('not_satisfied', 'Not Satisfied'),
    ], string="3. Filling attendance in Odoo and KPI?")
    q3_attendance_kpi = fields.Char(string="Q3 Explanation")

    q4_rating = fields.Selection([
        ('satisfied', 'Satisfied'),
        ('neutral', 'Neutral'),
        ('not_satisfied', 'Not Satisfied'),
    ], string="4. Getting guidance from the client?")
    q4_guidance = fields.Char(string="Q4 Explanation")

    q5_rating = fields.Selection([
        ('satisfied', 'Satisfied'),
        ('neutral', 'Neutral'),
        ('not_satisfied', 'Not Satisfied'),
    ], string="5. Using Hubstaff?")
    q5_hubstaff = fields.Char(string="Q5 Explanation")

    q6_rating = fields.Selection([
        ('satisfied', 'Satisfied'),
        ('neutral', 'Neutral'),
        ('not_satisfied', 'Not Satisfied'),
    ], string="6. Any challenges?")
    q6_challenges = fields.Char(string="Q6 Explanation")

    q7_rating = fields.Selection([
        ('satisfied', 'Satisfied'),
        ('neutral', 'Neutral'),
        ('not_satisfied', 'Not Satisfied'),
    ], string="7. What's your daily tasks and how many team members you have?")
    q7_daily_tasks = fields.Char(string="Q7 Explanation")

    selected_employee_ids = fields.Many2many(
        "hr.employee",
        "employee_meeting_mail_rel",
        "meeting_id",
        "employee_id",
        string="CC Mail To",
        help="Select employees who will receive the reason email if meeting status is Red or Yellow."
    )
    is_mail_sent = fields.Boolean(string="Mail Sent", readonly=True, tracking=True)

    action_taken_comment = fields.Char(string='Action Taken', tracking=True)
    action_employee_ids = fields.Many2many(
        "hr.employee",
        "employee_meeting_action_mail_rel",
        "meeting_id",
        "employee_id",
        string="Send Action Mail To",
        help="Employees who will receive the action taken update email."
    )
    is_action_mail_sent = fields.Boolean(string="Action Mail Sent", readonly=True, tracking=True)

    # ----------------------------
    # Send Reason Mail
    # ----------------------------
    def action_send_reason_mail(self):
        """Send email with reason, employee name, date, and record link to assignee (To:) and selected employees (CC:)"""
        for record in self:
            if record.meeting_status not in ['yellow', 'red']:
                raise UserError("You can only send emails for Red or Yellow meetings.")
            if not record.reason:
                raise UserError("Please mention a reason before sending the email.")
            if not record.assignee_id or not record.assignee_id.work_email:
                raise UserError("Please assign an employee (with a work email) as the task assignee.")
            if not record.selected_employee_ids:
                raise UserError("Please select employees to CC in the email.")

            # Get base URL for record link
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            record_url = f"{base_url}/web#id={record.id}&model=employee.probation.meeting&view_type=form"

            # Email subject and body
            subject = f"Probation Meeting Update for {record.employee_id.name}"
            body = f"""
                <div style="font-family:Arial, sans-serif; line-height:1.6;">
                    <h3 style="color:#004080;">Probation Meeting Summary</h3>
                    <p>Hi <b>{record.assignee_id.name}</b>,</p>
                    <p>You have been assigned the following probation review task:</p>
                    <p><b>Employee:</b> {record.employee_id.name}</p>
                    <p><b>Meeting Date:</b> {record.date_meeting.strftime('%d-%m-%Y')}</p>
                    <p><b>Probation Type:</b> {record.probation_type.replace('_', ' ').title()} Probation</p>
                    <p><b>Meeting Status:</b>
                        <span style="color:{'green' if record.meeting_status == 'green' else 'orange' if record.meeting_status == 'yellow' else 'red'};">
                            {record.meeting_status.capitalize()}
                        </span>
                    </p>
                    <p><b>Reason:</b> {record.reason}</p>
                    <p>You can view the full meeting record here:
                        <a href="{record_url}" target="_blank">View in Odoo</a>
                    </p>
                    <br/>
                    <p style="color:#666;">--<br/>Sent automatically from Odoo HR System</p>
                </div>
            """

            # Build CC list (comma-separated)
            cc_emails = ','.join(emp.work_email for emp in record.selected_employee_ids if emp.work_email)

            # Prepare mail
            mail_values = {
                'subject': subject,
                'body_html': body,
                'email_to': record.assignee_id.work_email,
                'email_cc': cc_emails,
            }

            # Send email
            self.env['mail.mail'].sudo().create(mail_values).send()
            record.is_mail_sent = True


    def action_send_action_mail(self):
        for record in self:
            if not record.action_taken_comment:
                raise UserError("Please write the action taken before sending the email.")
            if not record.action_employee_ids:
                raise UserError("Please select employees to send this update to.")

            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            record_url = f"{base_url}/web#id={record.id}&model=employee.probation.meeting&view_type=form"

            subject = f"Action Taken Update for {record.employee_id.name}'s Probation Meeting"
            body = f"""
                <div style="font-family:Arial, sans-serif; line-height:1.6;">
                    <h3 style="color:#004080;">Probation Meeting Action Update</h3>
                    <p><b>Employee:</b> {record.employee_id.name}</p>
                    <p><b>Date:</b> {record.date_meeting.strftime('%d-%m-%Y')}</p>
                    <p><b>Action Taken:</b> {record.action_taken_comment}</p>
                    <p>You can view this meeting record in Odoo:
                        <a href="{record_url}" target="_blank">View Record</a>
                    </p>
                </div>
            """

            mail_sent = False
            for emp in record.action_employee_ids:
                if not emp.work_email:
                    continue
                self.env['mail.mail'].sudo().create({
                    'subject': subject,
                    'body_html': body,
                    'email_to': emp.work_email,
                }).send()
                mail_sent = True

            if mail_sent:
                record.is_action_mail_sent = True