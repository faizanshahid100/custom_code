from odoo import models, fields

class DepartmentMaster(models.Model):
    _name = 'department.master'
    _description = 'Department Master'
    _rec_name = 'name'

    name = fields.Char(string='Department Name', required=True)
