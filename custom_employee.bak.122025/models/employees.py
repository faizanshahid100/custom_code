# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HREmployeeInherit(models.Model):
    _inherit = 'hr.employee'

    employee_status = fields.Selection([('active', 'Active'),
                                        ('passive', 'Passive')],
                                       string='Employee Status', default='active', tracking=True)
    blood_group = fields.Selection([('a+', 'A+'), ('a-', 'A-'), ('b+', 'B+'), ('b-', 'B-'), ('o+', 'O+'), ('o-', 'O-'),
                                    ('ab-', 'AB-'), ('ab+', 'AB+')],
                                   string='Blood Group', tracking=True)
    cnic_expiry = fields.Date(string="Identification Expiry")
    citizenship_id = fields.Char(string="Citizenship ID")
    province = fields.Char(string='Province')
    chronic_diseases = fields.Selection([('yes', 'Yes'),
                                         ('no', 'No')],
                                        string='Chronic Diseases', tracking=True)
    meds_in_use = fields.Selection([('yes', 'Yes'),
                                         ('no', 'No')],
                                        string='Meds in Use', tracking=True)
    signed = fields.Char(string='Signed')
    joining_date = fields.Date(string='Joining Date')
    confirmation_date = fields.Date(string='Confirmation Date')
    leaving_date = fields.Date(string='Leaving Date')
    joining_salary = fields.Integer(string='Joining Salary')
    current_salary = fields.Integer(string='Current Salary')
    emergency_contact_relation = fields.Char(string="Relation")
    emp_father_name = fields.Char(string="Father Name")
    emp_father_cnic = fields.Char(string="Father CNIC")
    next_to_kin = fields.Char(string="Next to Kin")
    next_to_kin_relation = fields.Char(string="Next to Kin Relation")
    reference_check = fields.Char(string="Reference Check")
    background_check = fields.Char(string="Background Check")
    credit_check = fields.Char(string="Credit Check")

    # One2Many Fields
    employee_contractor_info_ids = fields.One2many('employee.contractor.info', 'employee_id', string='Employee Contractor Info')
    employee_performance_ids = fields.One2many('employee.performance', 'employee_id', string='Employee Performance')
    employee_professional_info_ids = fields.One2many('employee.professional.info', 'employee_id', string='Employee Professional Info')
    health_insurance_info_ids = fields.One2many('health.insurance.info', 'employee_id', string='Health Insurance Info')
