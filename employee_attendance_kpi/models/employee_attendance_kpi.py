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
    department_id = fields.Many2one('hr.department', related='employee_id.department_id', store=True, string='Department')
    date = fields.Date(string='Date', required=True, default=fields.Date.today)
    
    # Week Number (Sprint)
    week_number = fields.Char(string='Week/Sprint', compute='_compute_week_number', store=True, 
                               help='Week number in format Sprint_1, Sprint_2, etc.')
    week_number_int = fields.Integer(string='Week Number', compute='_compute_week_number', store=True,
                                      help='Integer week number for sorting and filtering')
    
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

    @api.depends('date')
    def _compute_week_number(self):
        """
        Compute week number in format Sprint_X based on ISO week number
        Week starts on Monday (ISO standard)
        """
        for record in self:
            if record.date:
                # Get ISO week number (1-53)
                # isocalendar() returns (year, week, weekday)
                iso_year, iso_week, iso_weekday = record.date.isocalendar()
                
                # Format as Sprint_X
                record.week_number = f"Sprint_{iso_week}"
                record.week_number_int = iso_week
            else:
                record.week_number = "Sprint_0"
                record.week_number_int = 0

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

    def _update_weekly_record(self):
        """
        Update the corresponding weekly record when this daily record changes
        This ensures weekly records update in real-time
        """
        for record in self:
            if not record.date or not record.employee_id:
                continue
            
            # Get ISO week information
            iso_year, iso_week, _ = record.date.isocalendar()
            
            # Find corresponding weekly record
            weekly_record = self.env['employee.attendance.kpi.weekly'].search([
                ('employee_id', '=', record.employee_id.id),
                ('year', '=', iso_year),
                ('week_number_int', '=', iso_week),
            ], limit=1)
            
            if weekly_record:
                # Recompute all fields for the weekly record
                try:
                    weekly_record.recompute_all_fields()
                    _logger.debug(f"Updated weekly record for {record.employee_id.name} - Week {iso_week}")
                except Exception as e:
                    _logger.error(f"Error updating weekly record: {str(e)}")
            else:
                # Create weekly record if it doesn't exist
                try:
                    week_start, week_end = self.env['employee.attendance.kpi.weekly'].get_week_date_range(iso_year, iso_week)
                    new_weekly = self.env['employee.attendance.kpi.weekly'].create({
                        'employee_id': record.employee_id.id,
                        'year': iso_year,
                        'week_number': f"Sprint_{iso_week}",
                        'week_number_int': iso_week,
                        'week_start_date': week_start,
                        'week_end_date': week_end,
                        'total_days': 7,
                    })
                    _logger.info(f"Created weekly record for {record.employee_id.name} - Week {iso_week}")
                except Exception as e:
                    _logger.error(f"Error creating weekly record: {str(e)}")

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to update weekly records when new daily records are added"""
        records = super(EmployeeAttendanceKPI, self).create(vals_list)
        
        # Update corresponding weekly records
        records._update_weekly_record()
        
        return records

    def write(self, vals):
        """Override write to update weekly records when daily records are modified"""
        result = super(EmployeeAttendanceKPI, self).write(vals)
        
        # Update corresponding weekly records
        self._update_weekly_record()
        
        return result

    def unlink(self):
        """Override unlink to update weekly records when daily records are deleted"""
        # Store affected weekly records before deletion
        affected_weeks = []
        for record in self:
            if record.date and record.employee_id:
                iso_year, iso_week, _ = record.date.isocalendar()
                affected_weeks.append((record.employee_id.id, iso_year, iso_week))
        
        result = super(EmployeeAttendanceKPI, self).unlink()
        
        # Update affected weekly records
        for employee_id, year, week in affected_weeks:
            weekly_record = self.env['employee.attendance.kpi.weekly'].search([
                ('employee_id', '=', employee_id),
                ('year', '=', year),
                ('week_number_int', '=', week),
            ], limit=1)
            
            if weekly_record:
                try:
                    weekly_record.recompute_all_fields()
                    _logger.debug(f"Updated weekly record after deletion - Week {week}")
                except Exception as e:
                    _logger.error(f"Error updating weekly record after deletion: {str(e)}")
        
        return result

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
    def update_last_n_days_records(self, days=30):
        """
        Update attendance KPI records for the last N days
        This ensures that retroactive entries are properly reflected
        """
        _logger.info(f"Updating attendance KPI records for the last {days} days")
        
        today = fields.Date.today()
        start_date = today - timedelta(days=days)
        
        # Get all active employees
        employees = self.env['hr.employee'].search([('active', '=', True)])
        
        updated_count = 0
        created_count = 0
        
        for employee in employees:
            # Process each day in the range
            current_date = start_date
            while current_date <= today:
                # Check if record exists
                existing_record = self.search([
                    ('employee_id', '=', employee.id),
                    ('date', '=', current_date),
                ])
                
                if existing_record:
                    # Update existing record
                    try:
                        # Recompute attendance type
                        existing_record._compute_attendance_type()
                        # Fetch latest KPI data
                        existing_record.fetch_kpi_data_from_daily_progress()
                        # Force recompute KPI percentage
                        existing_record._compute_kpi_percentage()
                        updated_count += 1
                    except Exception as e:
                        _logger.error(f"Error updating record for {employee.name} on {current_date}: {str(e)}")
                else:
                    # Create new record for past date
                    try:
                        record = self.create({
                            'employee_id': employee.id,
                            'date': current_date,
                        })
                        record.fetch_kpi_data_from_daily_progress()
                        created_count += 1
                    except Exception as e:
                        _logger.error(f"Error creating record for {employee.name} on {current_date}: {str(e)}")
                
                current_date += timedelta(days=1)
        
        _logger.info(f"Updated {updated_count} records and created {created_count} new records for the last {days} days")
        return True

    @api.model
    def cron_create_daily_records(self):
        """
        Cron method to create daily records and update last 30 days
        This ensures both new records are created and retroactive data is updated
        """
        # Create today's records
        self.create_daily_records()
        
        if datetime.today().weekday() == 4:
            self.update_last_n_days_records(days=15)
        
        return True
