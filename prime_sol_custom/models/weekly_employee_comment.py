# -*- coding: utf-8 -*-
from odoo import models, fields

class WeeklyEmployeeComment(models.Model):
    _name = 'weekly.employee.comment'
    _description = 'Weekly Employee Comments'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    from_date = fields.Date('From Date', required=True)
    to_date = fields.Date('To Date', required=True)
    comment = fields.Text('Comment')
    
    _sql_constraints = [
        ('unique_employee_week', 'unique(employee_id, from_date, to_date)', 
         'Only one comment per employee per week is allowed!')
    ]
