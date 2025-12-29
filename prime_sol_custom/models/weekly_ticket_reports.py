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
    employment_type = fields.Selection(
        [("permanent", "Permanent"), ("contract", "Contract"), ("intern", "Internship"), ], string="Employment Type",
        default='permanent')
    working_hours_type = fields.Selection([('peak', 'Peak Hours'), ('off', 'Off Hours')], string="Working Hours Type",
                                          default='peak')
    comments = fields.Text('Comments')

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

    # Week comment fields (computed from weekly.employee.comment)
    week_1_comment = fields.Text(string='W1 Comment', compute='_compute_week_comments', inverse='_inverse_week_1_comment')
    week_2_comment = fields.Text(string='W2 Comment', compute='_compute_week_comments', inverse='_inverse_week_2_comment')
    week_3_comment = fields.Text(string='W3 Comment', compute='_compute_week_comments', inverse='_inverse_week_3_comment')
    week_4_comment = fields.Text(string='W4 Comment', compute='_compute_week_comments', inverse='_inverse_week_4_comment')
    week_5_comment = fields.Text(string='W5 Comment', compute='_compute_week_comments', inverse='_inverse_week_5_comment')
    week_6_comment = fields.Text(string='W6 Comment', compute='_compute_week_comments', inverse='_inverse_week_6_comment')
    week_7_comment = fields.Text(string='W7 Comment', compute='_compute_week_comments', inverse='_inverse_week_7_comment')
    week_8_comment = fields.Text(string='W8 Comment', compute='_compute_week_comments', inverse='_inverse_week_8_comment')
    week_9_comment = fields.Text(string='W9 Comment', compute='_compute_week_comments', inverse='_inverse_week_9_comment')
    week_10_comment = fields.Text(string='W10 Comment', compute='_compute_week_comments', inverse='_inverse_week_10_comment')
    week_11_comment = fields.Text(string='W11 Comment', compute='_compute_week_comments', inverse='_inverse_week_11_comment')
    week_12_comment = fields.Text(string='W12 Comment', compute='_compute_week_comments', inverse='_inverse_week_12_comment')
    week_13_comment = fields.Text(string='W13 Comment', compute='_compute_week_comments', inverse='_inverse_week_13_comment')
    week_14_comment = fields.Text(string='W14 Comment', compute='_compute_week_comments', inverse='_inverse_week_14_comment')
    week_15_comment = fields.Text(string='W15 Comment', compute='_compute_week_comments', inverse='_inverse_week_15_comment')
    week_16_comment = fields.Text(string='W16 Comment', compute='_compute_week_comments', inverse='_inverse_week_16_comment')
    week_17_comment = fields.Text(string='W17 Comment', compute='_compute_week_comments', inverse='_inverse_week_17_comment')
    week_18_comment = fields.Text(string='W18 Comment', compute='_compute_week_comments', inverse='_inverse_week_18_comment')
    week_19_comment = fields.Text(string='W19 Comment', compute='_compute_week_comments', inverse='_inverse_week_19_comment')
    week_20_comment = fields.Text(string='W20 Comment', compute='_compute_week_comments', inverse='_inverse_week_20_comment')
    week_21_comment = fields.Text(string='W21 Comment', compute='_compute_week_comments', inverse='_inverse_week_21_comment')
    week_22_comment = fields.Text(string='W22 Comment', compute='_compute_week_comments', inverse='_inverse_week_22_comment')
    week_23_comment = fields.Text(string='W23 Comment', compute='_compute_week_comments', inverse='_inverse_week_23_comment')
    week_24_comment = fields.Text(string='W24 Comment', compute='_compute_week_comments', inverse='_inverse_week_24_comment')
    week_25_comment = fields.Text(string='W25 Comment', compute='_compute_week_comments', inverse='_inverse_week_25_comment')
    week_26_comment = fields.Text(string='W26 Comment', compute='_compute_week_comments', inverse='_inverse_week_26_comment')

    # Store week ranges for computation
    week_ranges = fields.Text('Week Ranges', help='JSON string of week date ranges')

    @api.depends('employee_id', 'week_ranges')
    def _compute_week_comments(self):
        for record in self:
            # Initialize all comment fields
            for i in range(1, 27):
                setattr(record, f'week_{i}_comment', '')
            
            if not record.employee_id or not record.week_ranges:
                continue
                
            import json
            try:
                ranges = json.loads(record.week_ranges)
                comments = self.env['weekly.employee.comment'].search([
                    ('employee_id', '=', record.employee_id.id)
                ])
                
                for i, (start_str, end_str) in enumerate(ranges, 1):
                    if i > 26:
                        break
                    start_date = fields.Date.from_string(start_str)
                    end_date = fields.Date.from_string(end_str)
                    
                    comment = comments.filtered(
                        lambda c: c.from_date == start_date and c.to_date == end_date
                    )
                    setattr(record, f'week_{i}_comment', comment.comment if comment else '')
                    
            except (json.JSONDecodeError, ValueError, TypeError):
                pass

    def _get_week_dates(self, week_num):
        """Get start and end dates for a specific week"""
        if not self.week_ranges:
            return None, None
        import json
        try:
            ranges = json.loads(self.week_ranges)
            if week_num <= len(ranges):
                start_str, end_str = ranges[week_num - 1]
                return fields.Date.from_string(start_str), fields.Date.from_string(end_str)
        except (json.JSONDecodeError, ValueError, TypeError, IndexError):
            pass
        return None, None

    def _save_week_comment(self, week_num, comment):
        """Save comment for a specific week"""
        if not self.employee_id:
            return
        start_date, end_date = self._get_week_dates(week_num)
        if not start_date or not end_date:
            return
            
        existing = self.env['weekly.employee.comment'].search([
            ('employee_id', '=', self.employee_id.id),
            ('from_date', '=', start_date),
            ('to_date', '=', end_date)
        ])
        
        if existing:
            existing.comment = comment or ''
        elif comment:
            self.env['weekly.employee.comment'].create({
                'employee_id': self.employee_id.id,
                'from_date': start_date,
                'to_date': end_date,
                'comment': comment
            })

    # Inverse methods for each week
    def _inverse_week_1_comment(self): 
        for record in self: record._save_week_comment(1, record.week_1_comment)
    def _inverse_week_2_comment(self): 
        for record in self: record._save_week_comment(2, record.week_2_comment)
    def _inverse_week_3_comment(self): 
        for record in self: record._save_week_comment(3, record.week_3_comment)
    def _inverse_week_4_comment(self): 
        for record in self: record._save_week_comment(4, record.week_4_comment)
    def _inverse_week_5_comment(self): 
        for record in self: record._save_week_comment(5, record.week_5_comment)
    def _inverse_week_6_comment(self): 
        for record in self: record._save_week_comment(6, record.week_6_comment)
    def _inverse_week_7_comment(self): 
        for record in self: record._save_week_comment(7, record.week_7_comment)
    def _inverse_week_8_comment(self): 
        for record in self: record._save_week_comment(8, record.week_8_comment)
    def _inverse_week_9_comment(self): 
        for record in self: record._save_week_comment(9, record.week_9_comment)
    def _inverse_week_10_comment(self): 
        for record in self: record._save_week_comment(10, record.week_10_comment)
    def _inverse_week_11_comment(self): 
        for record in self: record._save_week_comment(11, record.week_11_comment)
    def _inverse_week_12_comment(self): 
        for record in self: record._save_week_comment(12, record.week_12_comment)
    def _inverse_week_13_comment(self): 
        for record in self: record._save_week_comment(13, record.week_13_comment)
    def _inverse_week_14_comment(self): 
        for record in self: record._save_week_comment(14, record.week_14_comment)
    def _inverse_week_15_comment(self): 
        for record in self: record._save_week_comment(15, record.week_15_comment)
    def _inverse_week_16_comment(self): 
        for record in self: record._save_week_comment(16, record.week_16_comment)
    def _inverse_week_17_comment(self): 
        for record in self: record._save_week_comment(17, record.week_17_comment)
    def _inverse_week_18_comment(self): 
        for record in self: record._save_week_comment(18, record.week_18_comment)
    def _inverse_week_19_comment(self): 
        for record in self: record._save_week_comment(19, record.week_19_comment)
    def _inverse_week_20_comment(self): 
        for record in self: record._save_week_comment(20, record.week_20_comment)
    def _inverse_week_21_comment(self): 
        for record in self: record._save_week_comment(21, record.week_21_comment)
    def _inverse_week_22_comment(self): 
        for record in self: record._save_week_comment(22, record.week_22_comment)
    def _inverse_week_23_comment(self): 
        for record in self: record._save_week_comment(23, record.week_23_comment)
    def _inverse_week_24_comment(self): 
        for record in self: record._save_week_comment(24, record.week_24_comment)
    def _inverse_week_25_comment(self): 
        for record in self: record._save_week_comment(25, record.week_25_comment)
    def _inverse_week_26_comment(self): 
        for record in self: record._save_week_comment(26, record.week_26_comment)

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        """Override search to exclude records for employees who were absent or on leave"""
        # Get employees who were present (had attendance records)
        present_employees = self.env['hr.attendance'].search([]).mapped('employee_id.id')

        # Add domain to filter only present employees
        if present_employees:
            args = args + [('employee_id', 'in', present_employees)]
        else:
            # If no attendance records, return empty result
            args = args + [('id', '=', False)]

        return super().search(args, offset=offset, limit=limit, order=order, count=count)