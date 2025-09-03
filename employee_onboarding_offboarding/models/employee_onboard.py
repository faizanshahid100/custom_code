from odoo import api, fields, models, _
from odoo.exceptions import AccessError, ValidationError
from datetime import timedelta

class EmployeeOnboard(models.Model):
    _name = "employee.onboard"
    _rec_name = "employee_id"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Employee Onboard"


    sequence = fields.Char('Sequence', readonly=True, copy=False, index=True, default=lambda self: _('New'))
    employee_id = fields.Many2one('hr.employee', string='Employee')
    date = fields.Date('Date', default=fields.Date.today)
    joining_date = fields.Date("Joining Date", required=True, tracking=True)
    state = fields.Selection([('inprogress', 'In-Progress'), ('completed', 'Completed')],
                             string='Request Status', default='inprogress', tracking=True)
    department_id = fields.Many2one('hr.department', string='Department',related='employee_id.department_id')
    job_id = fields.Many2one('hr.job', string='Job Position',related='employee_id.job_id')
    parent_id = fields.Many2one('hr.employee', string='Manager', related='employee_id.parent_id')
    checklist_template_id = fields.Many2one('checklist.template', string='Checklist Template', tracking=True)
    hr_responsible = fields.Many2one('hr.employee', string='Hr Responsible')
    request_ids = fields.One2many('checklist.requests', 'onboard_id', string='Requests')

    def action_set_inprogress(self):
        self.state = 'inprogress'

    def action_set_completed(self):
        self.state = 'completed'

    @api.model
    def create(self, vals):
        # Generate Sequence
        if vals.get('sequence', _('New')) == _('New'):
            vals['sequence'] = self.env['ir.sequence'].next_by_code('employee.onboard') or _('New')

        record = super(EmployeeOnboard, self).create(vals)

        # --- Auto-create Checklist Requests from Template ---
        template = self.env['checklist.template'].search([
            ('type', '=', 'onboarding'),
            ('active', '=', True),
            ('id', '=', record.checklist_template_id.id)
        ], limit=1)
        if template:
            if template.hr_responsible:
                record.hr_responsible = template.hr_responsible.id

        if template and template.line_ids:
            request_lines = []
            for line in template.line_ids:
                request_lines.append({
                    'employee_id': record.employee_id.id,
                    'request': line.requirement,
                    'user_id': line.responsible_user_id.id,
                    'assigned_date': fields.Date.today(),
                    'expected_date': record.joining_date - timedelta(days=line.due_days),
                    'state': 'todo',
                    'onboard_id': record.id,
                })
            requests = self.env['checklist.requests'].create(request_lines)

            # --- Send mail to employee for each task ---
            for req in requests:
                if req.employee_id.work_email:  # only if employee has email
                    subject = f"New Onboarding Task Assigned - {req.request}"
                    body = f"""
                                    <p>Dear {req.user_id.name},</p>
                                    <p>A new Pre-Onboarding task has been assigned to you:</p>
                                    <ul>
                                        <li><b>Task:</b> {req.request}</li>
                                        <li><b>Assigned By:</b> {'System Auto Generated Task'}</li>
                                        <li><b>Expected Completion Date:</b> {req.expected_date.strftime('%d %B %Y')}</li>
                                    </ul>
                                    <p>Please complete this task before the due date.</p>
                                    <br/>
                                    <p>Regards,<br/>HR Team</p>
                                """
                    mail_values = {
                        "subject": subject,
                        "body_html": body,
                        "email_from": "hr@primesystemsolutions.com",
                        "email_to": req.user_id.login,
                    }
                    self.env["mail.mail"].sudo().create(mail_values).send()

        return record


class ChecklistRequests(models.Model):
    _name = "checklist.requests"
    _rec_name = "employee_id"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Checklist Requests"

    employee_id = fields.Many2one('hr.employee', string='Employee')
    request = fields.Char('Request')
    user_id = fields.Many2one('res.users', string='Responsible Person')
    assigned_date = fields.Date('Assigned Date')
    expected_date = fields.Date('Expected Date')
    state = fields.Selection([('todo', 'Todo'),
                                        ('inprogress', 'In-Progress'),('completed', 'Completed')],
                                       string='Request Status', default='todo', tracking=True)
    onboard_id = fields.Many2one('employee.onboard', 'Checklist')

    def action_set_todo(self):
        self.state = 'todo'
        self._update_onboard_state()

    def action_set_inprogress(self):
        self.state = 'inprogress'
        self._update_onboard_state()

    def action_set_completed(self):
        self.state = 'completed'
        self._update_onboard_state()

    def _update_onboard_state(self):
        """Update parent onboard state when all requests are completed"""
        for rec in self:
            if rec.onboard_id:
                all_completed = all(line.state == 'completed' for line in rec.onboard_id.request_ids)
                if all_completed and rec.onboard_id.state != 'completed':
                    rec.onboard_id.state = 'completed'
                elif not all_completed and rec.onboard_id.state == 'completed':
                    # rollback to inprogress if any request is reopened
                    rec.onboard_id.state = 'inprogress'