# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class EmployeeAttendanceKPIWeeklyBusiness(models.Model):
    _name = 'employee.attendance.kpi.weekly.business'
    _description = 'Employee Weekly Business KPI Records'
    _order = 'year desc, week_number_int desc, employee_id'
    _rec_name = 'display_name'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, ondelete='cascade')
    department_id = fields.Many2one('hr.department', related='employee_id.department_id', store=True, string='Department')
    year = fields.Integer(string='Year', required=True)
    week_number = fields.Char(string='Week/Sprint', required=True, help='Week number in format Sprint_X')
    week_number_int = fields.Integer(string='Week Number', required=True, help='Integer week number for sorting')

    # Week Date Range
    week_start_date = fields.Date(string='Week Start', required=True)
    week_end_date = fields.Date(string='Week End', required=True)

    # Business KPI Count
    kpi_count = fields.Integer(
        string='KPI Count',
        compute='_compute_kpi_count',
        store=True,
        help='Number of records created in daily.progress.business during this week by the employee'
    )

    # Display name
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=True)

    _sql_constraints = [
        ('unique_employee_week_year_business',
         'UNIQUE(employee_id, year, week_number_int)',
         'Only one weekly business record per employee per week is allowed!')
    ]

    @api.depends('employee_id', 'year', 'week_number')
    def _compute_display_name(self):
        for record in self:
            if record.employee_id and record.week_number:
                record.display_name = f"{record.employee_id.name} - {record.week_number} ({record.year})"
            else:
                record.display_name = "New Weekly Business Record"

    @api.depends('employee_id', 'week_start_date', 'week_end_date')
    def _compute_kpi_count(self):
        """Count daily.progress.business records created by the employee within the week range"""
        for record in self:
            if not record.employee_id or not record.week_start_date or not record.week_end_date:
                record.kpi_count = 0
                continue

            user = record.employee_id.user_id
            if not user:
                record.kpi_count = 0
                continue

            count = self.env['daily.progress.business'].search_count([
                ('resource_user_id', '=', user.id),
                ('date_of_project', '>=', record.week_start_date),
                ('date_of_project', '<=', record.week_end_date),
            ])

            record.kpi_count = count

    def recompute_all_fields(self):
        """Force recompute all computed fields"""
        for record in self:
            record._compute_kpi_count()
        return True

    @api.model
    def get_week_date_range(self, year, week_number):
        """Get the start and end date for a given ISO week"""
        jan_4 = datetime(year, 1, 4)
        week_1_start = jan_4 - timedelta(days=jan_4.weekday())
        week_start = week_1_start + timedelta(weeks=week_number - 1)
        week_end = week_start + timedelta(days=6)
        return week_start.date(), week_end.date()

    @api.model
    def create_weekly_business_records(self, year=None, week_number=None):
        """Create or update weekly business records for all active employees"""
        if year is None or week_number is None:
            today = fields.Date.today()
            year, week_number, _ = today.isocalendar()

        _logger.info(f"Creating weekly business KPI records for {year} - Week {week_number}")

        week_start, week_end = self.get_week_date_range(year, week_number)
        employees = self.env['hr.employee'].search([('active', '=', True), ("department_id.name", "ilike", "Business")])
        created_records = self.env['employee.attendance.kpi.weekly.business']

        for employee in employees:
            existing = self.search([
                ('employee_id', '=', employee.id),
                ('year', '=', year),
                ('week_number_int', '=', week_number),
            ])

            if existing:
                existing.recompute_all_fields()
                created_records |= existing
                continue

            try:
                record = self.create({
                    'employee_id': employee.id,
                    'year': year,
                    'week_number': f"Sprint_{week_number}",
                    'week_number_int': week_number,
                    'week_start_date': week_start,
                    'week_end_date': week_end,
                })
                created_records |= record
                _logger.info(f"Created weekly business record for {employee.name} - Week {week_number}")
            except Exception as e:
                _logger.error(f"Error creating weekly business record for {employee.name}: {str(e)}")

        return created_records

    @api.model
    def update_last_n_weeks_records(self, weeks=4):
        """Update weekly business records for the last N weeks"""
        today = fields.Date.today()
        current_year, current_week, _ = today.isocalendar()

        for i in range(weeks):
            week_num = current_week - i
            year = current_year

            if week_num <= 0:
                year -= 1
                dec_31 = datetime(year, 12, 31)
                _, weeks_in_year, _ = dec_31.isocalendar()
                week_num = weeks_in_year + week_num

            try:
                self.create_weekly_business_records(year=year, week_number=week_num)
            except Exception as e:
                _logger.error(f"Error updating weekly business record for week {week_num} of {year}: {str(e)}")

        return True

    @api.model
    def cron_create_weekly_business_records(self):
        """Cron method to create/update weekly business records"""
        self.create_weekly_business_records()
        self.update_last_n_weeks_records(weeks=4)
        return True
