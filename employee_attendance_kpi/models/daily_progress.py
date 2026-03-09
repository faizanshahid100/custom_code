# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class DailyProgress(models.Model):
    _inherit = 'daily.progress'

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to update attendance KPI records when new KPI data is added"""
        records = super(DailyProgress, self).create(vals_list)
        
        # Update attendance KPI records for affected dates
        self._update_attendance_kpi_records(records)
        
        return records

    def write(self, vals):
        """Override write to update attendance KPI records when KPI data is modified"""
        result = super(DailyProgress, self).write(vals)
        
        # Check if KPI-related fields were updated
        kpi_fields = ['avg_resolved_ticket', 'no_calls_duration', 'billable_hours', 'avg_resolution_time']
        if any(field in vals for field in kpi_fields):
            self._update_attendance_kpi_records(self)
        
        return result

    def unlink(self):
        """Override unlink to update attendance KPI records when KPI data is deleted"""
        # Store affected records before deletion
        affected_records = [(rec.resource_user_id, rec.date_of_project) for rec in self if rec.resource_user_id and rec.date_of_project]
        
        result = super(DailyProgress, self).unlink()
        
        # Update attendance KPI records for affected dates
        for user, date in affected_records:
            employee = self.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
            if employee:
                self._update_single_attendance_kpi(employee, date)
        
        return result

    def _update_attendance_kpi_records(self, progress_records):
        """Update attendance KPI records for the given daily progress records"""
        AttendanceKPI = self.env['employee.attendance.kpi']
        
        for progress in progress_records:
            if not progress.resource_user_id or not progress.date_of_project:
                continue
            
            # Get employee from user
            employee = self.env['hr.employee'].search([
                ('user_id', '=', progress.resource_user_id.id)
            ], limit=1)
            
            if not employee:
                _logger.warning(f"No employee found for user {progress.resource_user_id.name}")
                continue
            
            self._update_single_attendance_kpi(employee, progress.date_of_project)

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
                # Update existing record - fetch new KPI data
                kpi_record.fetch_kpi_data_from_daily_progress()
                kpi_record._compute_kpi_percentage()
                _logger.info(f"Updated KPI data for {employee.name} on {date}")
            else:
                # Create new record
                new_record = AttendanceKPI.create({
                    'employee_id': employee.id,
                    'date': date,
                })
                new_record.fetch_kpi_data_from_daily_progress()
                _logger.info(f"Created attendance KPI record with KPI data for {employee.name} on {date}")
                
        except Exception as e:
            _logger.error(f"Error updating KPI data for {employee.name} on {date}: {str(e)}")
