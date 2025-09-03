from odoo import fields, models, api, _

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