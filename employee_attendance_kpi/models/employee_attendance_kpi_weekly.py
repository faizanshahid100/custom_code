# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class EmployeeAttendanceKPIWeekly(models.Model):
    _name = 'employee.attendance.kpi.weekly'
    _description = 'Employee Weekly Attendance and KPI Tracking'
    _order = 'year desc, week_number_int desc, employee_id'
    _rec_name = 'display_name'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, ondelete='cascade')
    year = fields.Integer(string='Year', required=True)
    week_number = fields.Char(string='Week/Sprint', required=True, help='Week number in format Sprint_X')
    week_number_int = fields.Integer(string='Week Number', required=True, help='Integer week number for sorting')
    
    # Week Date Range
    week_start_date = fields.Date(string='Week Start Date', required=True)
    week_end_date = fields.Date(string='Week End Date', required=True)
    
    # Attendance Summary
    total_days = fields.Integer(string='Total Days', default=7, help='Total days in the week (usually 7)')
    working_days = fields.Integer(string='Working Days', compute='_compute_attendance_summary', store=True,
                                   help='Total working days (excluding weekends and holidays)')
    present_days = fields.Integer(string='Present Days', compute='_compute_attendance_summary', store=True)
    absent_days = fields.Integer(string='Absent Days', compute='_compute_attendance_summary', store=True)
    leave_days = fields.Integer(string='Leave Days', compute='_compute_attendance_summary', store=True)
    weekend_days = fields.Integer(string='Weekend Days', compute='_compute_attendance_summary', store=True)
    gazetted_days = fields.Integer(string='Gazetted Holiday Days', compute='_compute_attendance_summary', store=True)
    
    # Attendance Percentage
    attendance_percentage = fields.Float(string='Attendance %', compute='_compute_attendance_percentage', store=True,
                                         help='(Present Days / Working Days) * 100')
    
    # KPI Totals (Sum of week)
    total_tickets_resolved = fields.Integer(string='Total Tickets Resolved', 
                                            compute='_compute_kpi_totals', store=True)
    total_CAST = fields.Integer(string='Total CAST', compute='_compute_kpi_totals', store=True)
    total_billable_hours = fields.Integer(string='Total Billable Hours', 
                                          compute='_compute_kpi_totals', store=True)
    total_resolution_time = fields.Float(string='Total Response Time', 
                                         compute='_compute_kpi_totals', store=True,
                                         help='Sum of all response times for the week')
    
    # Weekly KPI Performance
    weekly_kpi_percentage = fields.Float(string='Weekly KPI Performance %', 
                                         compute='_compute_weekly_kpi_percentage', store=True,
                                         help='Weighted average KPI achievement for the week')
    
    # Display name
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=True)
    
    _sql_constraints = [
        ('unique_employee_week_year', 'UNIQUE(employee_id, year, week_number_int)', 
         'Only one weekly record per employee per week is allowed!')
    ]

    @api.depends('employee_id', 'year', 'week_number')
    def _compute_display_name(self):
        for record in self:
            if record.employee_id and record.week_number:
                record.display_name = f"{record.employee_id.name} - {record.week_number} ({record.year})"
            else:
                record.display_name = "New Weekly Record"

    @api.depends('employee_id', 'year', 'week_number_int')
    def _compute_attendance_summary(self):
        """Compute attendance summary from daily records"""
        for record in self:
            if not record.employee_id or not record.year or not record.week_number_int:
                record.working_days = 0
                record.present_days = 0
                record.absent_days = 0
                record.leave_days = 0
                record.weekend_days = 0
                record.gazetted_days = 0
                continue
            
            # Get daily records for this week
            daily_records = self.env['employee.attendance.kpi'].search([
                ('employee_id', '=', record.employee_id.id),
                ('date', '>=', record.week_start_date),
                ('date', '<=', record.week_end_date),
            ])
            
            # Count by attendance type
            present = daily_records.filtered(lambda r: r.attendance_type == 'present')
            absent = daily_records.filtered(lambda r: r.attendance_type == 'absent')
            leave = daily_records.filtered(lambda r: r.attendance_type == 'leave')
            weekend = daily_records.filtered(lambda r: r.attendance_type == 'weekend')
            gazetted = daily_records.filtered(lambda r: r.attendance_type == 'gazetted')
            
            record.present_days = len(present)
            record.absent_days = len(absent)
            record.leave_days = len(leave)
            record.weekend_days = len(weekend)
            record.gazetted_days = len(gazetted)
            
            # Working days = Total days - weekends - gazetted holidays
            record.working_days = record.total_days - record.weekend_days - record.gazetted_days

    @api.depends('present_days', 'working_days')
    def _compute_attendance_percentage(self):
        """Calculate attendance percentage"""
        for record in self:
            if record.working_days > 0:
                record.attendance_percentage = (record.present_days / record.working_days) * 100
            else:
                record.attendance_percentage = 0.0

    @api.depends('employee_id', 'year', 'week_number_int')
    def _compute_kpi_totals(self):
        """Compute KPI totals from daily records"""
        for record in self:
            if not record.employee_id or not record.year or not record.week_number_int:
                record.total_tickets_resolved = 0
                record.total_CAST = 0
                record.total_billable_hours = 0
                record.total_resolution_time = 0.0
                continue
            
            # Get daily records for this week
            daily_records = self.env['employee.attendance.kpi'].search([
                ('employee_id', '=', record.employee_id.id),
                ('date', '>=', record.week_start_date),
                ('date', '<=', record.week_end_date),
            ])
            
            # Sum totals
            record.total_tickets_resolved = sum(daily_records.mapped('ticket_resolved'))
            record.total_CAST = sum(daily_records.mapped('CAST'))
            record.total_billable_hours = sum(daily_records.mapped('billable_hours'))
            record.total_resolution_time = sum(daily_records.mapped('avg_resolution_time'))

    @api.depends('employee_id', 'total_tickets_resolved', 'total_CAST', 'total_billable_hours', 'total_resolution_time')
    def _compute_weekly_kpi_percentage(self):
        """
        Calculate weekly KPI percentage based on weekly targets in hr.employee
        Uses the same weighted approach as daily records
        Queries fresh data directly to avoid computed field dependency issues
        """
        for record in self:
            if not record.employee_id or not record.week_start_date or not record.week_end_date:
                record.weekly_kpi_percentage = 0.0
                continue
            
            employee = record.employee_id
            
            # Get weekly KPI targets from employee
            working_days = record.present_days or record.working_days or 1

            weekly_ticket_target = (employee.ticket_resolved or 0)
            weekly_CAST_target = (employee.CAST or 0) * working_days
            weekly_billable_hours_target = (employee.billable_hours or 0) * working_days
            weekly_response_time_target = (employee.avg_resolution_time or 0) * working_days
            
            # Count assigned KPIs (target > 0)
            assigned_kpis = []
            kpi_targets = {}
            
            if weekly_ticket_target > 0:
                assigned_kpis.append('ticket_resolved')
                kpi_targets['ticket_resolved'] = weekly_ticket_target
            if weekly_CAST_target > 0:
                assigned_kpis.append('CAST')
                kpi_targets['CAST'] = weekly_CAST_target
            if weekly_billable_hours_target > 0:
                assigned_kpis.append('billable_hours')
                kpi_targets['billable_hours'] = weekly_billable_hours_target
            if weekly_response_time_target > 0:
                assigned_kpis.append('avg_resolution_time')
                kpi_targets['avg_resolution_time'] = weekly_response_time_target
            
            num_assigned = len(assigned_kpis)
            
            if num_assigned == 0:
                record.weekly_kpi_percentage = 0.0
                continue
            
            # Get actual values directly from daily records (fresh query)
            daily_records = self.env['employee.attendance.kpi'].sudo().search([
                ('employee_id', '=', record.employee_id.id),
                ('date', '>=', record.week_start_date),
                ('date', '<=', record.week_end_date),
            ])
            
            if not daily_records:
                record.weekly_kpi_percentage = 0.0
                continue
            
            # Calculate actuals directly from daily records (all as sums/totals)
            total_tickets = 0
            total_CAST = 0
            total_billable_hours = 0
            total_resolution_time = 0.0
            
            for daily in daily_records:
                total_tickets += daily.ticket_resolved or 0
                total_CAST += daily.CAST or 0
                total_billable_hours += daily.billable_hours or 0
                total_resolution_time += daily.avg_resolution_time or 0.0
            
            # Calculate weight per KPI
            weight_per_kpi = 100.0 / num_assigned
            
            total_percentage = 0.0
            
            # Calculate percentage for each assigned KPI
            for kpi_name in assigned_kpis:
                target = kpi_targets[kpi_name]
                
                if kpi_name == 'ticket_resolved':
                    actual = total_tickets
                elif kpi_name == 'CAST':
                    actual = total_CAST
                elif kpi_name == 'billable_hours':
                    actual = total_billable_hours
                elif kpi_name == 'avg_resolution_time':
                    actual = total_resolution_time
                else:
                    actual = 0
                
                if target > 0:
                    # Calculate achievement percentage (cap at 100%)
                    if kpi_name == 'avg_resolution_time':
                        if actual > 0:
                            kpi_achievement = min(100.0, (float(target) / float(actual)) * 100.0)
                    else:
                        kpi_achievement = min(100.0, (float(actual) / float(target)) * 100.0)
                    # Add weighted contribution to total
                    total_percentage += (kpi_achievement * weight_per_kpi / 100.0)
            
            record.weekly_kpi_percentage = round(total_percentage, 2)
            
            # Debug logging
            _logger.debug(f"Weekly KPI % for {employee.name} Week {record.week_number}: "
                         f"Tickets={total_tickets}/{kpi_targets.get('ticket_resolved', 0)}, "
                         f"CAST={total_CAST}/{kpi_targets.get('CAST', 0)}, "
                         f"Hours={total_billable_hours}/{kpi_targets.get('billable_hours', 0)}, "
                         f"TotalResponseTime={total_resolution_time}/{kpi_targets.get('avg_resolution_time', 0)}, "
                         f"Result={record.weekly_kpi_percentage}%")

    @api.model
    def get_week_date_range(self, year, week_number):
        """
        Get the start and end date for a given ISO week
        Returns tuple (start_date, end_date)
        """
        # ISO week starts on Monday
        # Week 1 is the first week with a Thursday
        jan_4 = datetime(year, 1, 4)
        week_1_start = jan_4 - timedelta(days=jan_4.weekday())
        
        # Calculate the start of the target week
        week_start = week_1_start + timedelta(weeks=week_number - 1)
        week_end = week_start + timedelta(days=6)
        
        return week_start.date(), week_end.date()

    @api.model
    def create_weekly_records(self, year=None, week_number=None):
        """
        Create or update weekly records for all active employees
        If year and week_number not provided, uses current week
        """
        if year is None or week_number is None:
            today = fields.Date.today()
            year, week_number, _ = today.isocalendar()
        
        _logger.info(f"Creating weekly attendance KPI records for {year} - Week {week_number}")
        
        # Get week date range
        week_start, week_end = self.get_week_date_range(year, week_number)
        
        # Get all active employees
        employees = self.env['hr.employee'].search([('active', '=', True)])
        
        created_records = self.env['employee.attendance.kpi.weekly']
        
        for employee in employees:
            # Check if record already exists
            existing_record = self.search([
                ('employee_id', '=', employee.id),
                ('year', '=', year),
                ('week_number_int', '=', week_number),
            ])
            
            if existing_record:
                _logger.debug(f"Weekly record already exists for {employee.name} - Week {week_number}")
                # Force recompute all fields to get latest data
                existing_record.recompute_all_fields()
                created_records |= existing_record
                continue
            
            # Create new record
            try:
                record = self.create({
                    'employee_id': employee.id,
                    'year': year,
                    'week_number': f"Sprint_{week_number}",
                    'week_number_int': week_number,
                    'week_start_date': week_start,
                    'week_end_date': week_end,
                    'total_days': 7,
                })
                
                created_records |= record
                _logger.info(f"Created weekly attendance KPI record for {employee.name} - Week {week_number}")
            except Exception as e:
                _logger.error(f"Error creating weekly record for {employee.name}: {str(e)}")
        
        _logger.info(f"Created/Updated {len(created_records)} weekly attendance KPI records for Week {week_number}")
        return created_records

    @api.model
    def update_last_n_weeks_records(self, weeks=4):
        """
        Update weekly attendance KPI records for the last N weeks
        """
        _logger.info(f"Updating weekly attendance KPI records for the last {weeks} weeks")
        
        today = fields.Date.today()
        current_year, current_week, _ = today.isocalendar()
        
        updated_count = 0
        
        for i in range(weeks):
            # Calculate week number (going backwards)
            week_num = current_week - i
            year = current_year
            
            # Handle year boundary
            if week_num <= 0:
                year -= 1
                # Get number of weeks in previous year
                dec_31 = datetime(year, 12, 31)
                _, weeks_in_year, _ = dec_31.isocalendar()
                week_num = weeks_in_year + week_num
            
            try:
                self.create_weekly_records(year=year, week_number=week_num)
                updated_count += 1
            except Exception as e:
                _logger.error(f"Error updating week {week_num} of year {year}: {str(e)}")
        
        _logger.info(f"Updated {updated_count} weeks of weekly attendance KPI records")
        return True

    @api.model
    def cron_create_weekly_records(self):
        """Cron method to create/update weekly records"""
        # Create current week
        self.create_weekly_records()
        
        # Update last 4 weeks to catch any changes
        self.update_last_n_weeks_records(weeks=4)
        
        return True

    def recompute_all_fields(self):
        """
        Force recompute all computed fields for the weekly record
        Useful after daily data changes
        """
        for record in self:
            # Force recompute by invalidating cache and computing
            record._compute_attendance_summary()
            record._compute_attendance_percentage()
            record._compute_kpi_totals()
            record._compute_weekly_kpi_percentage()
            
        return True
