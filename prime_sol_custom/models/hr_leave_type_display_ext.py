# -*- coding: utf-8 -*-

from odoo import api, fields, models

class HrLeaveTypeDisplayExt(models.Model):
    _inherit = "hr.leave.type"

    def name_get(self):
        result = []
        employee_id = self.env.context.get('employee_id') or self.env.user.employee_id.id
        
        for leave_type in self:
            name = leave_type.name
            
            if employee_id:
                if leave_type.requires_allocation == 'yes':
                    # Use existing computed field for leaves taken
                    leave_type_with_context = leave_type.with_context(employee_id=employee_id)
                    taken = leave_type_with_context.leaves_taken
                else:
                    # For unpaid/no allocation leaves, sum the days from hr.leave
                    leaves = self.env['hr.leave'].search([
                        ('employee_id', '=', employee_id),
                        ('holiday_status_id', '=', leave_type.id),
                        ('state', '=', 'validate')
                    ])
                    taken = sum(leaves.mapped('number_of_days'))
                
                name = f"{name} ({int(taken)})"
            
            result.append((leave_type.id, name))
        
        return result
