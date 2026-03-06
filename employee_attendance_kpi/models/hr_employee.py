# -*- coding: utf-8 -*-
from odoo import models, fields, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    
    # Count of assigned KPIs
    assigned_kpi_count = fields.Integer(
        string='Assigned KPIs',
        compute='_compute_assigned_kpi_count',
        store=True,
        help='Number of KPIs assigned to this employee'
    )
    
    # Attendance KPI Records
    attendance_kpi_ids = fields.One2many(
        'employee.attendance.kpi',
        'employee_id',
        string='Attendance & KPI Records'
    )

    @api.depends('ticket_resolved', 'CAST', 'billable_hours', 'avg_resolution_time')
    def _compute_assigned_kpi_count(self):
        """Count how many KPIs are assigned (target > 0)"""
        for employee in self:
            count = 0
            if employee.ticket_resolved > 0:
                count += 1
            if employee.CAST > 0:
                count += 1
            if employee.billable_hours > 0:
                count += 1
            if employee.avg_resolution_time > 0:
                count += 1
            
            employee.assigned_kpi_count = count
