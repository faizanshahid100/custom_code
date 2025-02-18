# -*- coding: utf-8 -*-
from odoo import models, fields, api


class EmployeeContractorInfo(models.Model):
    _name = 'employee.contractor.info'
    _description = 'Employee Contractor Info'

    employee_id = fields.Many2one('hr.employee', string="Employees")
    contractor = fields.Char(string="Contractor")
    contractor_id = fields.Char(string="ID")
    business_unit = fields.Char(string="Business Unit")
    pl_code = fields.Char(string="PL Code")
    department = fields.Char(string="Dept")
    manager = fields.Char(string="Manager (Contractor)")
    dept_hod = fields.Char(string="Dept HOD")
    serving_region = fields.Char(string="Serving Region")
    shift_time = fields.Char(string="Shift Time")
    job_title = fields.Char(string="Job Time")
    level = fields.Char(string="Level")
    working_location = fields.Char(string="Working Location")
    rotation_based = fields.Char(string="Rotation Based")
    pss_group = fields.Selection([
        ('technical', 'Technical'),
        ('non_technical', 'Non-Technical'),
    ], string='PSS Group')
    contract_type = fields.Many2one('hr.contract', string="Rotation Based")
    contract_start = fields.Date(string="Contract Start")
    contract_end = fields.Date(string="Contract End")
    work_mode = fields.Selection([
        ('onsite', 'Onsite'),
        ('hybrid', 'Hybrid'),
        ('fully_remote', 'Fully Remote'),
    ], string='Work Mode')