# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class EmployeeAttendanceKPI(models.Model):
    _name = 'employee.attendance.kpi'
    _description = 'Employee Attendance and KPI Tracking'
    _order = 'date desc, employee_id'
    _rec_name = 'display_name'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, ondelete='cascade')
    date = fields.Date(string='Date', required=True, default=fields.Date.today)
    
    # Attendance Type
    attendance_type = fields.Selection([
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('leave', 'Leave'),
        ('weekend', 'Weekend'),
        ('gazetted', 'Gazetted Holiday'),
    ], string='Attendance Type', compute='_compute_attendance_type', store=True)
    
    # KPI Fields from daily.progress
    ticket_resolved = fields.Integer(string='Resolved Tickets', default=0)
    CAST = fields.Integer(string='Calls', default=0)
    billable_hours = fields.Integer(string='Billable Hours', default=0)
    avg_resolution_time = fields.Float(string='Response Time (Avg)', default=0.0)
    
    # KPI Percentage (Weighted Average)
    kpi_percentage = fields.Float(string='KPI Performance %', compute='_compute_kpi_percentage', store=True)
    
    # Display name
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=True)
    
    _sql_constraints = [
        ('unique_employee_date', 'UNIQUE(employee_id, date)', 'Only one record per employee per date is allowed!')
    ]

    @api.depends('employee_id', 'date')
    def _compute_display_name(self):
        for record in self:
            if record.employee_id and record.date:
                record.display_name = f"{record.employee_id.name} - {record.date}"
            else:
                record.display_name = "New Record"

    @api.depends('employee_id', 'date')
    def _compute_attendance_type(self):
        """
        Compute attendance type based on the following priority:
        1. Weekend - if employee has weekend on that day
        2. Gazetted - if there's a gazetted holiday
        3. Leave - if employee has approved leave
        4. Present - if employee has attendance record
        5. Absent - default if none of the above
        """
        for record in self:
            if not record.employee_id or not record.date:
                record.attendance_type = 'absent'
                continue
            
            # Check for Weekend
            if self._is_weekend(record.employee_id, record.date):
                record.attendance_type = 'weekend'
                continue
            
            # Check for Gazetted Holiday
            if str(record.date)in record.employee_id.sudo().gazetted_holiday_id.holiday_dates:
                record.attendance_type = 'gazetted'
                continue
            
            # Check for Approved Leave
            if self._has_approved_leave(record.employee_id, record.date):
                record.attendance_type = 'leave'
                continue
            
            # Check for Attendance (Present)
            if self._has_attendance(record.employee_id, record.date):
                record.attendance_type = 'present'
                continue
            
            # Default to Absent
            record.attendance_type = 'absent'

    def _is_weekend(self, employee, date):
        """Check if the given date is a weekend for the employee"""
        # Get employee's resource calendar
        calendar = employee.resource_calendar_id or self.env.company.resource_calendar_id
        
        if not calendar:
            # Default to Saturday and Sunday if no calendar
            return date.weekday() in [5, 6]
        
        # Check if the day is in the calendar's working days
        day_of_week = str(date.weekday())  # 0=Monday, 6=Sunday
        attendance_lines = calendar.attendance_ids.filtered(lambda a: a.dayofweek == day_of_week)
        
        return not attendance_lines

    def _has_approved_leave(self, employee, date):
        """Check if employee has approved leave on the given date"""
        leave = self.env['hr.leave'].search([
            ('employee_id', '=', employee.id),
            ('state', '=', 'validate'),
            ('date_from', '<=', datetime.combine(date, datetime.max.time())),
            ('date_to', '>=', datetime.combine(date, datetime.min.time())),
        ], limit=1)
        
        return bool(leave)

    def _has_attendance(self, employee, date):
        """Check if employee has attendance record for the given date"""
        attendance = self.env['hr.attendance'].search([
            ('employee_id', '=', employee.id),
            ('check_in', '>=', datetime.combine(date, datetime.min.time())),
            ('check_in', '<=', datetime.combine(date, datetime.max.time())),
        ], limit=1)
        
        return bool(attendance)

    @api.depends('ticket_resolved', 'CAST', 'billable_hours', 'avg_resolution_time', 'employee_id')
    def _compute_kpi_percentage(self):
        """
        Calculate weighted KPI percentage based on assigned KPIs in hr.employee
        Weight distribution:
        - 1 KPI assigned: 100%
        - 2 KPIs assigned: 50% each
        - 3 KPIs assigned: 33.33% each
        - 4 KPIs assigned: 25% each
        """
        for record in self:
            if not record.employee_id:
                record.kpi_percentage = 0.0
                continue
            
            employee = record.employee_id
            
            # Get KPI targets from employee
            kpi_targets = {
                'ticket_resolved': getattr(employee, 'ticket_resolved', 0) or 0,
                'CAST': getattr(employee, 'CAST', 0) or 0,
                'billable_hours': getattr(employee, 'billable_hours', 0) or 0,
                'avg_resolution_time': getattr(employee, 'avg_resolution_time', 0) or 0,
            }
            
            # Count assigned KPIs (target > 0)
            assigned_kpis = []
            
            if kpi_targets['ticket_resolved'] > 0:
                assigned_kpis.append('ticket_resolved')
            if kpi_targets['CAST'] > 0:
                assigned_kpis.append('CAST')
            if kpi_targets['billable_hours'] > 0:
                assigned_kpis.append('billable_hours')
            if kpi_targets['avg_resolution_time'] > 0:
                assigned_kpis.append('avg_resolution_time')
            
            num_assigned = len(assigned_kpis)
            
            if num_assigned == 0:
                record.kpi_percentage = 0.0
                continue
            
            # Calculate weight per KPI
            weight_per_kpi = 100.0 / num_assigned
            
            total_percentage = 0.0
            
            # Calculate percentage for each assigned KPI
            for kpi_name in assigned_kpis:
                target = kpi_targets[kpi_name]
                actual = getattr(record, kpi_name, 0) or 0
                
                if target > 0:
                    kpi_percentage = min(100.0, (actual / target) * 100)
                    total_percentage += (kpi_percentage * weight_per_kpi / 100.0)
            
            record.kpi_percentage = round(total_percentage, 2)

    def fetch_kpi_data_from_daily_progress(self):
        """Fetch KPI data from daily.progress model"""
        for record in self:
            if not record.employee_id or not record.date:
                continue
            
            # Search for daily progress record
            daily_progress = self.env['daily.progress'].search([
                ('resource_user_id', '=', record.employee_id.user_id.id),
                ('date_of_project', '=', record.date),
            ], limit=1)
            
            if daily_progress:
                record.ticket_resolved = daily_progress.avg_resolved_ticket or 0
                record.CAST = daily_progress.no_calls_duration or 0  # Assuming CAST is the field name
                record.billable_hours = daily_progress.billable_hours or 0
                record.avg_resolution_time = daily_progress.avg_resolution_time or 0.0
            else:
                record.ticket_resolved = 0
                record.CAST = 0
                record.billable_hours = 0
                record.avg_resolution_time = 0.0

    @api.model
    def create_daily_records(self, date=None):
        """
        Create daily attendance KPI records for all active employees
        This method should be called by a scheduled action
        """
        if date is None:
            date = fields.Date.today()
        
        _logger.info(f"Creating daily attendance KPI records for {date}")
        
        # Get all active employees
        employees = self.env['hr.employee'].search([('active', '=', True)])
        
        created_records = self.env['employee.attendance.kpi']
        
        for employee in employees:
            # Check if record already exists
            existing_record = self.search([
                ('employee_id', '=', employee.id),
                ('date', '=', date),
            ])
            
            if existing_record:
                _logger.debug(f"Record already exists for {employee.name} on {date}")
                # Update KPI data
                existing_record.fetch_kpi_data_from_daily_progress()
                created_records |= existing_record
                continue
            
            # Create new record
            try:
                record = self.create({
                    'employee_id': employee.id,
                    'date': date,
                })
                
                # Fetch KPI data
                record.fetch_kpi_data_from_daily_progress()
                
                created_records |= record
                _logger.info(f"Created attendance KPI record for {employee.name} on {date}")
            except Exception as e:
                _logger.error(f"Error creating record for {employee.name}: {str(e)}")
        
        _logger.info(f"Created {len(created_records)} attendance KPI records for {date}")
        return created_records

    @api.model
    def cron_create_daily_records(self):
        """Cron method to create daily records"""
        return self.create_daily_records()
