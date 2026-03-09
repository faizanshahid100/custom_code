# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    def _update_affected_weekly_records(self):
        """
        Update weekly records for all dates affected by this leave
        """
        for leave in self:
            if not leave.employee_id or not leave.date_from or not leave.date_to:
                continue
            
            # Get date range
            start_date = leave.date_from.date() if isinstance(leave.date_from, datetime) else leave.date_from
            end_date = leave.date_to.date() if isinstance(leave.date_to, datetime) else leave.date_to
            
            # Update daily records for each affected date (they will trigger weekly updates)
            current_date = start_date
            while current_date <= end_date:
                # Find daily record for this date
                daily_record = self.env['employee.attendance.kpi'].search([
                    ('employee_id', '=', leave.employee_id.id),
                    ('date', '=', current_date),
                ], limit=1)
                
                if daily_record:
                    # Trigger recomputation of attendance type
                    daily_record._compute_attendance_type()
                    # This will automatically trigger weekly record update via daily record's write()
                
                current_date += timedelta(days=1)

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to update weekly records when new leave is created"""
        records = super(HrLeave, self).create(vals_list)
        
        # Only update if leave is validated
        validated_leaves = records.filtered(lambda l: l.state == 'validate')
        if validated_leaves:
            validated_leaves._update_affected_weekly_records()
        
        return records

    def write(self, vals):
        """Override write to update weekly records when leave is modified"""
        result = super(HrLeave, self).write(vals)
        
        # Update if state changed to validate or if dates changed
        if 'state' in vals or 'date_from' in vals or 'date_to' in vals:
            validated_leaves = self.filtered(lambda l: l.state == 'validate')
            if validated_leaves:
                validated_leaves._update_affected_weekly_records()
        
        return result

    def unlink(self):
        """Override unlink to update weekly records when leave is deleted"""
        # Store affected data before deletion
        affected_data = []
        for leave in self:
            if leave.employee_id and leave.date_from and leave.date_to:
                start_date = leave.date_from.date() if isinstance(leave.date_from, datetime) else leave.date_from
                end_date = leave.date_to.date() if isinstance(leave.date_to, datetime) else leave.date_to
                affected_data.append((leave.employee_id.id, start_date, end_date))
        
        result = super(HrLeave, self).unlink()
        
        # Update affected daily records
        for employee_id, start_date, end_date in affected_data:
            current_date = start_date
            while current_date <= end_date:
                daily_record = self.env['employee.attendance.kpi'].search([
                    ('employee_id', '=', employee_id),
                    ('date', '=', current_date),
                ], limit=1)
                
                if daily_record:
                    daily_record._compute_attendance_type()
                    # This will trigger weekly record update
                
                current_date += timedelta(days=1)
        
        return result
