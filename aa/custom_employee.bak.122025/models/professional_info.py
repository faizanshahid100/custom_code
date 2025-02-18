# -*- coding: utf-8 -*-
from odoo import models, fields, api


class EmployeeProfessionalInfo(models.Model):
    _name = 'employee.professional.info'
    _description = 'Employee Professional Info'

    employee_id = fields.Many2one('hr.employee', string="Employees")
    last_degree = fields.Char(string="Last Degree")
    year_of_grade = fields.Integer(string="Year of Grade")
    school_college_uni = fields.Char(string="School/College/Uni")
    hec_attested = fields.Boolean(string="HEC Attested")
    no_of_exp = fields.Integer(string="No of Exp")
    area_of_expertise = fields.Char(string="Area of Expertise")
    previous_company = fields.Char(string="Previous Company")
