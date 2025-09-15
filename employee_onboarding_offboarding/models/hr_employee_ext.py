from odoo import fields, models, api, _
from datetime import date, timedelta


class HrEmployeeExt(models.Model):
    _inherit = 'hr.employee'

    checklist_template_id = fields.Many2one('checklist.template', string='Checklist Template', tracking=True)

    @api.model
    def create(self, vals):
        employee = super(HrEmployeeExt, self).create(vals)

        # Create onboard record automatically
        self.env['employee.onboard'].sudo().create({
            'employee_id': employee.id,
            'joining_date': employee.joining_date,
            'checklist_template_id': employee.checklist_template_id.id,
        })
        return employee

    def _cron_send_feedback_survey(self):
        # Employees whose joining_date was exactly 1 day ago
        one_day_after = date.today() - timedelta(days=1)
        employees = self.search([
            ('joining_date', '=', one_day_after),
            ('work_email', '!=', False)
        ])

        for emp in employees:
            subject = "How was your first day at Prime System Solutions?"
            body = f"""
                <p>Dear {emp.name},</p>
                <p>We hope your first day went smoothly and that you’re settling in well at Prime System Solutions.</p>
                <p>We’d love to hear about your onboarding experience so far. Your feedback will help us improve and make the process even better for future team members.</p>
                <p>Please click the Button below to complete the survey:</p>
                <br/>
                <p><a href="https://forms.office.com/r/DtGDQVcPh6"
                      style="background:#1e88e5;color:#fff;padding:10px 15px;text-decoration:none;border-radius:5px;">
                    Give Feedback
                </a></p>
                <br/>
                <p>Thank you for your time.<br/>
                <b>HR Team</b></p>
            """
            mail_values = {
                "subject": subject,
                "body_html": body,
                "email_from": "hr@primesystemsolutions.com",
                "email_to": emp.work_email,
            }
            self.env['mail.mail'].sudo().create(mail_values).send()

    def _cron_mid_probation_notify(self):
        today = fields.Date.today()
        employees = self.search([('joining_date', '!=', False), ('confirmation_date', '!=', False)])

        for emp in employees:
            if emp.joining_date and emp.confirmation_date:
                total_days = (emp.confirmation_date - emp.joining_date).days
                mid_date = emp.joining_date + timedelta(days=total_days // 2)

                if today == mid_date and emp.parent_id and emp.parent_id.work_email:
                    subject = f"Mid-Probation Review Reminder - {emp.name}"
                    body = f"""
                        <p>Dear {emp.parent_id.name},</p>
                        <p>This is a reminder to record mid-probation review notes in Odoo for your team member <b>{emp.name}</b>.</p>
                        <p>Please review their progress and provide feedback. HR will support with any training if needed.</p>
                        <br/>
                        <p>Regards,<br/>HR System</p>
                    """
                    self.env['mail.mail'].sudo().create({
                        'subject': subject,
                        'body_html': body,
                        'email_from': 'hr@primesystemsolutions.com',
                        'email_to': emp.parent_id.work_email,
                    }).send()

    def _cron_confirm_employee(self):
        pass