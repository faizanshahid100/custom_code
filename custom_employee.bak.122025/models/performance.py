# -*- coding: utf-8 -*-
from odoo import models, fields, api


class EmployeePerformance(models.Model):
    _name = 'employee.performance'
    _description = 'Employee Performance'

    employee_id = fields.Many2one('hr.employee', string="Employees")
    punctuality = fields.Integer(string="Punctuality")
    problem_solving = fields.Integer(string="Problem Solving")
    knowledge = fields.Integer(string="Knowledge")
    team_work = fields.Integer(string="Team Work")
    communication = fields.Integer(string="Communication")
    meet_kpi = fields.Integer(string="Meet Kpi's")
    avg_grande = fields.Integer(string="Avg Grade")
    month = fields.Integer(string="Month")
