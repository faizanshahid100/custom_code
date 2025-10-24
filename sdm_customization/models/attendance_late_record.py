# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import datetime, date, time, timedelta


class AttendanceLateRecord(models.Model):
    _name = 'attendance.late.record'
    _description = 'Daily Late Attendance Record'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    date = fields.Date(string='Date', required=True, default=fields.Date.context_today)
    minutes_overdue = fields.Integer(string='Total Late Minutes', readonly=True)
    remarks = fields.Char('Remarks')


    _sql_constraints = [
        ('unique_employee_date', 'unique(employee_id, date)', 'A record already exists for this employee and date!')
    ]
