from odoo import models, fields, api

class EmployeeScreenshot(models.Model):
    _name = "employee.screenshot"
    _description = "Employee Screenshot Records"

    name = fields.Char(default='User')
    user_id = fields.Many2one('res.users', string="User", required=True)
    timestamp = fields.Datetime(string="Captured At", required=True)
    screenshot = fields.Binary(string="Screenshot", attachment=True)
    filename = fields.Char(string="Filename")
