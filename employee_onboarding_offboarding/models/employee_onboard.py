from odoo import api, fields, models, _
from odoo.exceptions import AccessError, ValidationError

class EmployeeOnboard(models.Model):
    _name = "employee.onboard"
    _rec_name = "employee_id"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Employee Onboard"


    sequence = fields.Char('Sequence', readonly=True, copy=False, index=True, default=lambda self: _('New'))
    employee_id = fields.Many2one('hr.employee', string='Employee')
    date = fields.Date('Date')
    department_id = fields.Many2one('hr.department', string='Department',related='employee_id.department_id')
    job_id = fields.Many2one('hr.job', string='Job Position',related='employee_id.job_id')
    parent_id = fields.Many2one('hr.employee', string='Manager', related='employee_id.parent_id')
    hr_responsible = fields.Many2one('hr.employee', string='Hr Responsible')
    request_ids = fields.One2many('checklist.requests', 'onboard_id', string='Requests')

    @api.model
    def create(self, vals):
        if vals.get('sequence', _('New')) == _('New'):
            vals['sequence'] = self.env['ir.sequence'].next_by_code('employee.onboard') or _('New')
        return super(EmployeeOnboard, self).create(vals)



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
    state = fields.Selection([('draft', 'Draft'),
                                        ('inprogress', 'In-Progress'),('completed', 'Completed')],
                                       string='Request Status', default='draft', tracking=True)
    onboard_id = fields.Many2one('employee.onboard', 'Checklist')

    def action_set_draft(self):
        self.state = 'draft'

    def action_set_inprogress(self):
        self.state = 'inprogress'

    def action_set_completed(self):
        self.state = 'completed'