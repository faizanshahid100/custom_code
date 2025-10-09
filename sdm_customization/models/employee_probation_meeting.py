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
    ], string="Probation Type", required=True)

    meeting_status = fields.Selection([
        ("green", "Green"),
        ("yellow", "Yellow"),
        ("red", "Red"),
    ], string="Meeting Status", required=True, tracking=True)

    reason = fields.Text(string="Reason (If Yellow/Red)", help="Specify reason for concern if status is not Green")

    # Questions
    q1_experience = fields.Text(string="1. How is your experience going so far?")
    q2_alignment = fields.Text(string="2. Are you aligned with the client?")
    q3_attendance_kpi = fields.Text(string="3. Filling attendance in Odoo and KPI?")
    q4_guidance = fields.Text(string="4. Getting guidance from the client?")
    q5_hubstaff = fields.Text(string="5. Using Hubstaff?")
    q6_challenges = fields.Text(string="6. Any challenges?")
    q7_daily_tasks = fields.Text(string="7. What's your daily tasks and how many team members you have?")

    selected_employee_ids = fields.Many2many(
        "hr.employee", string="Send Mail To",
        help="Select employees who will receive the reason email if meeting status is Red or Yellow."
    )
    is_mail_sent = fields.Boolean(string="Mail Sent", readonly=True, tracking=True)

    def action_send_reason_mail(self):
        """Send email with reason, employee name, date, and record link to selected employees"""
        for record in self:
            if record.meeting_status not in ['yellow', 'red']:
                raise UserError("You can only send emails for Red or Yellow meetings.")
            if not record.reason:
                raise UserError("Please mention a reason before sending the email.")
            if not record.selected_employee_ids:
                raise UserError("Please select employees to notify.")

            # Get base URL
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            record_url = f"{base_url}/web#id={record.id}&model=employee.probation.meeting&view_type=form"

            subject = f"Probation Meeting Update for {record.employee_id.name}"

            body = f"""
                <div style="font-family:Arial, sans-serif; line-height:1.6;">
                    <h3 style="color:#004080;">Probation Meeting Summary</h3>
                    <p><b>Employee:</b> {record.employee_id.name}</p>
                    <p><b>Meeting Date:</b> {record.date_meeting.strftime('%d-%m-%Y')}</p>
                    <p><b>Probation Type:</b> {record.probation_type.replace('_', ' ').title()}</p>
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

            mail_sent = False
            for emp in record.selected_employee_ids:
                if not emp.work_email:
                    continue
                mail_values = {
                    'subject': subject,
                    'body_html': body,
                    'email_to': emp.work_email,
                }
                self.env['mail.mail'].sudo().create(mail_values).send()
                mail_sent = True

            # ✅ Mark checkbox if at least one email was sent
            if mail_sent:
                record.is_mail_sent = True
