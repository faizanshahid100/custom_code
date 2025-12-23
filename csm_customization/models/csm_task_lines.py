from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import date


class CSMTaskLines(models.Model):
    _name = 'csm.task.lines'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = 'CSM Task Assignment Lines'

    handbook_id = fields.Many2one('csm.handbook', string='CSM Handbook', ondelete='cascade')
    reason = fields.Text('Reason Details', tracking=True)
    action_taken_comment = fields.Text('Action Taken', tracking=True)
    
    to_employee_ids = fields.Many2many(
        "hr.employee",
        "csm_task_assign_to_rel",
        "task_id",
        "employee_id",
        string="To", tracking=True
    )

    cc_employee_ids = fields.Many2many(
        "hr.employee",
        "csm_task_assign_cc_rel",
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
            if not record.handbook_id:
                raise UserError("No CSM handbook linked with this task line.")

            # Generate record URL
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            record_url = f"{base_url}/web#id={record.handbook_id.id}&model=csm.handbook&view_type=form"

            subject = f"Action Taken Update for {record.handbook_id.customer_id.name}'s CSM Meeting"
            body = f"""
                <div style="font-family:Arial, sans-serif; line-height:1.6;">
                    <h3 style="color:#004080;">CSM Meeting Action Update</h3>
                    # <p><b>Task Completed:</b> ✅</p>
                    <p><b>Customer:</b> {record.handbook_id.customer_id.name}</p>
                    <p><b>Manager:</b> {record.handbook_id.manager_id.name or 'N/A'}</p>
                    <p><b>Action Taken:</b> {record.action_taken_comment or 'Resolved'}</p>
                    <p>You can view this CSM record in Odoo:
                        <a href="{record_url}" target="_blank">View Record</a>
                    </p>
                </div>
            """

            # Send to manager and current user
            to_emails = []
            if record.handbook_id.manager_email:
                to_emails.append(record.handbook_id.manager_email)
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
