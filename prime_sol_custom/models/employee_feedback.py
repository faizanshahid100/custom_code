from odoo import models, fields, api, _
from datetime import date
from odoo.exceptions import UserError, ValidationError


class EmployeeFeedback(models.Model):
    _name = 'hr.employee.feedback'
    _rec_name = 'employee_id'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = 'Employee Feedback'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, readonly=False)
    date_feedback = fields.Date(string='Date', required=True)
    client_id = fields.Many2one('res.partner', string='Client Name', required=True, domain=[('is_company', '=', True)])
    manager_id = fields.Many2one('res.partner', string='Manager')
    manager = fields.Char(string='Manager')
    manager_email = fields.Char(string='Manager Email', store=True, readonly=False)
    current_meeting_frequency = fields.Selection([
        ('monthly', 'Monthly'),
        ('bi_monthly', 'Bi-Monthly'),
        ('weekly', 'Weekly'),
        ('bi_weekly', 'Bi-Weekly'),
        ('tbd', 'TBD'),
        ('not_required', 'Not Required')
    ], string='Current Meeting Frequency', store=True, readonly=False)
    business_tech = fields.Char(string='Business/Tech', store=True, readonly=False)
    client_feedback = fields.Text('Client Feedback', required=True)
    month = fields.Date(string='Month')
    current_month_schedule = fields.Datetime(string='Current Month Schedule')
    feedback_type = fields.Selection([
        ('positive', 'Positive'),
        ('negative', 'Negative'),
        ('positive_neutral', 'Positive Neutral'),
        ('negative_neutral', 'Negative Neutral'),
    ], string='Feedback Type', required=True)
    gar = fields.Selection([
        ("green", "Green"),
        ("yellow", "Yellow"),
        ("red", "Red"),
    ], string="Employee Status", default='green', required=True, tracking=True)
    outcome_suggested = fields.Text(string='Outcome Suggested')
    next_followup_date = fields.Date(string='Next Follow-up')
    feedback_status = fields.Selection([
        ('casual', 'Casual'),
        ('inprogress', 'Inprogress'),
        ('resolved', 'Resolved'),
    ], string="Feedback Status", default='casual', required=True)
    comment = fields.Text()
    is_meeting_done = fields.Boolean(string='Is Meeting Done?')
    is_meeting_rescheduled = fields.Boolean(string='Is Meeting Rescheduled?')
    task_assign_line_ids = fields.One2many('employee.feedback.task.lines', 'feedback_id', string='Task Assignment Lines')

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        for rec in self:
            if not rec.employee_id:
                rec.client_id = False
                rec.manager = False
                rec.manager_email = ''
                rec.business_tech = False
                return

            employee = rec.employee_id

            # Client from contractor
            contractor = employee.contractor
            rec.client_id = contractor.id if contractor else False

            # Manager from contractor child
            rec.manager = employee.manager if employee else ''
            rec.manager_email = employee.manager_email if employee else ''
            rec.business_tech = employee.department_id.name if employee.department_id else False

    # ----------------------------
    # Send Reason Mail
    # ----------------------------
    def action_send_reason_mail(self):
        """Send email with reason, employee name, date, and record link to assignee (To:) and selected employees (CC:)"""
        for record in self.task_assign_line_ids.filtered(lambda l: not l.csm_task_confirmed):
            if not record.reason:
                raise UserError("Please mention a reason before sending the email.")
            if not record.to_employee_ids or not any(emp.work_email for emp in record.to_employee_ids):
                raise UserError("Please assign an employee (with a work email) as the task assignee.")

            # Get base URL for record link
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            record_url = f"{base_url}/web#id={self.id}&model=hr.employee.feedback&view_type=form"

            # Email subject and body
            subject = f"CSM Meeting Update for {self.employee_id.name}"
            body = f"""
                <div style="font-family:Arial, sans-serif; line-height:1.6;">
                    <h3 style="color:#004080;">CSM Meeting Summary</h3>
                    <p>Hi <b>{", ".join(record.to_employee_ids.mapped("name"))}</b>,</p>
                    <p>You have been assigned the following CSM review task:</p>
                    <p><b>Employee:</b> {self.employee_id.name}</p>
                    <p><b>Meeting Date:</b> {self.date_feedback.strftime('%d-%m-%Y')}</p>
                    <p><b>Reason:</b> {record.reason}</p>
                    <p><b>Priority:</b> {'⭐' * int(record.priority)}</p>
                    <p>You can view the full meeting record here:
                        <a href="{record_url}" target="_blank">View in Odoo</a>
                    </p>
                    <br/>
                    <p style="color:#666;">--<br/>Sent automatically from Odoo CSM Team</p>
                </div>
            """

            # Build CC list from selected employees
            to_emails = [emp.work_email for emp in record.to_employee_ids if emp.work_email]
            cc_emails = [emp.work_email for emp in record.cc_employee_ids if emp.work_email]

            # Add default CC for users in the "Managers" security group
            manager_group = self.env.ref('prime_sol_custom.prime_group_managers', raise_if_not_found=False)
            if manager_group:
                manager_users = manager_group.users.filtered(lambda u: u.partner_id.email)
                cc_emails.extend([u.partner_id.email for u in manager_users])

            # Remove duplicates and join into comma-separated string
            to_emails = ','.join(set(to_emails))
            cc_emails = ','.join(set(cc_emails))

            # Prepare mail
            mail_values = {
                'subject': subject,
                'body_html': body,
                'email_from': 'hr@primesystemsolutions.com',
                'email_to': to_emails,
                'email_cc': cc_emails,
            }

            # Send email
            self.env['mail.mail'].sudo().create(mail_values).send()


class CSMTaskLines(models.Model):
    _name = 'employee.feedback.task.lines'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = 'Employee Feedback Task Assignment Lines'

    feedback_id = fields.Many2one('hr.employee.feedback', string='CSM Handbook', ondelete='cascade')
    reason = fields.Text('Reason Details', tracking=True)
    action_taken_comment = fields.Text('Action Taken', tracking=True)
    employee_task_confirmed = fields.Boolean(string="Employee Confirmed", tracking=True)

    to_employee_ids = fields.Many2many(
        "hr.employee",
        "employee_feedback_task_assign_to_rel",
        "task_id",
        "employee_id",
        string="To", tracking=True
    )

    cc_employee_ids = fields.Many2many(
        "hr.employee",
        "employee_feedback_task_assign_cc_rel",
        "task_id",
        "employee_id",
        string="CC", tracking=True
    )

    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Medium'),
        ('2', 'High'),
        ('3', 'Very High'),
    ], string="Task Priority", default='1', tracking=True)

    assign_date = fields.Date('Assign Date', default=lambda self: date.today(), tracking=True)
    csm_task_confirmed = fields.Boolean(string="CSM Confirmed", tracking=True)
    confirmed_date = fields.Date(string="Confirmation Date", default=fields.Date.today, tracking=True)

    @api.onchange('csm_task_confirmed')
    def _onchange_csm_task_confirmed(self):
        for rec in self:
            if rec.csm_task_confirmed:
                rec.confirmed_date = fields.Date.today()

    def action_send_action_mail(self):
        for record in self:
            if not record.employee_task_confirmed:
                raise UserError("Please mark 'Employee Confirmed' before sending the email.")
            if not record.feedback_id:
                raise UserError("No CSM handbook linked with this task line.")

            # Generate record URL
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            record_url = f"{base_url}/web#id={record.feedback_id.id}&model=hr.employee.feedback&view_type=form"

            subject = f"Action Taken Update for {record.feedback_id.client_id.name}'s CSM Meeting"
            body = f"""
                <div style="font-family:Arial, sans-serif; line-height:1.6;">
                    <h3 style="color:#004080;">CSM Meeting Action Update</h3>
                    <p><b>Task Completed:</b> ✅</p>
                    <p><b>Customer:</b> {record.feedback_id.client_id.name}</p>
                    <p><b>Manager:</b> {record.feedback_id.manager or 'N/A'}</p>
                    <p><b>Action Taken:</b> {record.action_taken_comment or 'Resolved'}</p>
                    <p>You can view this CSM record in Odoo:
                        <a href="{record_url}" target="_blank">View Record</a>
                    </p>
                </div>
            """

            # Send to manager and current user
            to_emails = []
            if record.feedback_id.manager_email:
                to_emails.append(record.feedback_id.manager_email)
            if self.env.user.partner_id.email:
                to_emails.append(self.env.user.partner_id.email)

            if not to_emails:
                raise UserError("No email addresses found to send notification.")

            # Send email
            self.env['mail.mail'].sudo().create({
                'subject': subject,
                'body_html': body,
                'email_from': 'csm@primesystemsolutions.com',
                'email_to': ','.join(set(to_emails)),
            }).send()

            record.confirmed_date = fields.Date.today()

        return True
