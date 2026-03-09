# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to update attendance KPI records when new attendance is added"""
        records = super(HrAttendance, self).create(vals_list)
        
        # Update attendance KPI records for affected dates
        self._update_attendance_kpi_records(records)
        
        return records

    def write(self, vals):
        """Override write to update attendance KPI records when attendance is modified"""
        result = super(HrAttendance, self).write(vals)
        
        # Update attendance KPI records for affected dates
        self._update_attendance_kpi_records(self)
        
        return result

    def unlink(self):
        """Override unlink to update attendance KPI records when attendance is deleted"""
        # Store affected records before deletion
        affected_records = [(rec.employee_id, rec.check_in.date()) for rec in self if rec.check_in]
        
        result = super(HrAttendance, self).unlink()
        
        # Update attendance KPI records for affected dates
        for employee, date in affected_records:
            self._update_single_attendance_kpi(employee, date)
        
        return result

    def _update_attendance_kpi_records(self, attendance_records):
        """Update attendance KPI records for the given attendance records"""
        AttendanceKPI = self.env['employee.attendance.kpi']
        
        for attendance in attendance_records:
            if not attendance.check_in:
                continue
            
            # Get the date from check_in
            attendance_date = attendance.check_in.date()
            employee = attendance.employee_id
            
            self._update_single_attendance_kpi(employee, attendance_date)

    def _update_single_attendance_kpi(self, employee, date):
        """Update or create a single attendance KPI record"""
        AttendanceKPI = self.env['employee.attendance.kpi']
        
        try:
            # Search for existing record
            kpi_record = AttendanceKPI.search([
                ('employee_id', '=', employee.id),
                ('date', '=', date),
            ], limit=1)
            
            if kpi_record:
                # Update existing record
                kpi_record._compute_attendance_type()
                kpi_record.fetch_kpi_data_from_daily_progress()
                kpi_record._compute_kpi_percentage()
                _logger.info(f"Updated attendance KPI for {employee.name} on {date}")
            else:
                # Create new record
                new_record = AttendanceKPI.create({
                    'employee_id': employee.id,
                    'date': date,
                })
                new_record.fetch_kpi_data_from_daily_progress()
                _logger.info(f"Created attendance KPI for {employee.name} on {date}")
                
        except Exception as e:
            _logger.error(f"Error updating attendance KPI for {employee.name} on {date}: {str(e)}")
