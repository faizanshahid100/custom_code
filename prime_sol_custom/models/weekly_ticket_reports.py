# -*- coding: utf-8 -*-
from email.policy import default

from odoo import models, fields, api
from datetime import date, timedelta

class WeeklyTicketReport(models.Model):
    _name = 'weekly.ticket.report'
    _description = 'Weekly Ticket Report'

    employee_id = fields.Many2one('hr.employee', string='Employee')
    job_position = fields.Char(related='employee_id.job_id.name', string='Job Position', store=True)
    department = fields.Char(related='employee_id.department_id.name', string='Department', store=True)
    contractor = fields.Char(related='employee_id.contractor.name', string='Contractor', store=True)
    contractor_manager = fields.Char(related='employee_id.manager', string='Manager (Contractor)', store=True)
    manager = fields.Char(related='employee_id.parent_id.name', string='Manager', store=True)
    gender = fields.Selection(related='employee_id.gender', string='Gender', store=True)
    level = fields.Char(related='employee_id.level', string='Level', store=True)

    # Week fields for 6 months (26 weeks)
    week_1 = fields.Char(string='W 1', default=' ')
    week_2 = fields.Char(string='W 2', default=' ')
    week_3 = fields.Char(string='W 3', default=' ')
    week_4 = fields.Char(string='W 4', default=' ')
    week_5 = fields.Char(string='W 5', default=' ')
    week_6 = fields.Char(string='W 6', default=' ')
    week_7 = fields.Char(string='W 7', default=' ')
    week_8 = fields.Char(string='W 8', default=' ')
    week_9 = fields.Char(string='W 9', default=' ')
    week_10 = fields.Char(string='W 10', default=' ')
    week_11 = fields.Char(string='W 11', default=' ')
    week_12 = fields.Char(string='W 12', default=' ')
    week_13 = fields.Char(string='W 13', default=' ')
    week_14 = fields.Char(string='W 14', default=' ')
    week_15 = fields.Char(string='W 15', default=' ')
    week_16 = fields.Char(string='W 16', default=' ')
    week_17 = fields.Char(string='W 17', default=' ')
    week_18 = fields.Char(string='W 18', default=' ')
    week_19 = fields.Char(string='W 19', default=' ')
    week_20 = fields.Char(string='W 20', default=' ')
    week_21 = fields.Char(string='W 21', default=' ')
    week_22 = fields.Char(string='W 22', default=' ')
    week_23 = fields.Char(string='W 23', default=' ')
    week_24 = fields.Char(string='W 24', default=' ')
    week_25 = fields.Char(string='W 25', default=' ')
    week_26 = fields.Char(string='W 26', default=' ')
    week_total = fields.Char(string='Total Counts', default=' ')