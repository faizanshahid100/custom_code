# -*- coding: utf-8 -*-
from odoo import models, fields, api


class HealthInsuranceInfo(models.Model):
    _name = 'health.insurance.info'
    _description = 'Health Insurance Info'

    employee_id = fields.Many2one('hr.employee', string="Employees")
    spouse_name = fields.Char(string="Spouse Name")
    spouse_cnic = fields.Char(string="Spouse CNIC")
    spouse_dob = fields.Date(string="Spouse DOB")
    child_name = fields.Char(string="Child Name")
    child_relation = fields.Char(string="Child Relation")
    child_dob = fields.Date(string="Child DOB")
