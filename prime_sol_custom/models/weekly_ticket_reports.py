# -*- coding: utf-8 -*-
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
    week_1 = fields.Char(string='Week 1')
    week_2 = fields.Char(string='Week 2')
    week_3 = fields.Char(string='Week 3')
    week_4 = fields.Char(string='Week 4')
    week_5 = fields.Char(string='Week 5')
    week_6 = fields.Char(string='Week 6')
    week_7 = fields.Char(string='Week 7')
    week_8 = fields.Char(string='Week 8')
    week_9 = fields.Char(string='Week 9')
    week_10 = fields.Char(string='Week 10')
    week_11 = fields.Char(string='Week 11')
    week_12 = fields.Char(string='Week 12')
    week_13 = fields.Char(string='Week 13')
    week_14 = fields.Char(string='Week 14')
    week_15 = fields.Char(string='Week 15')
    week_16 = fields.Char(string='Week 16')
    week_17 = fields.Char(string='Week 17')
    week_18 = fields.Char(string='Week 18')
    week_19 = fields.Char(string='Week 19')
    week_20 = fields.Char(string='Week 20')
    week_21 = fields.Char(string='Week 21')
    week_22 = fields.Char(string='Week 22')
    week_23 = fields.Char(string='Week 23')
    week_24 = fields.Char(string='Week 24')
    week_25 = fields.Char(string='Week 25')
    week_26 = fields.Char(string='Week 26')
    week_total = fields.Char(string='Total Counts', default=' ')