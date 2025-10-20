from odoo import models, fields, api

class HrEmployeeExt(models.Model):
    _inherit = 'hr.employee'

    employee_pulse_id = fields.Many2one('employee.pulse.profile', string="Employee Pulse")

    @api.model
    def create(self, vals):
        employee = super(HrEmployeeExt, self).create(vals)
        employee_pulse = self.env['employee.pulse.profile'].create({'employee_id': employee.id})
        employee.write({'employee_pulse_id': employee_pulse.id})
        return employee
