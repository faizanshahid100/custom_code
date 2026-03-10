# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class DailyProgressBusiness(models.Model):
    _inherit = 'daily.progress.business'

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to update weekly business records when new business KPI data is added"""
        records = super(DailyProgressBusiness, self).create(vals_list)
        self._update_weekly_business_records(records)
        return records

    def write(self, vals):
        """Override write to update weekly business records when business KPI data is modified"""
        result = super(DailyProgressBusiness, self).write(vals)
        self._update_weekly_business_records(self)
        return result

    def unlink(self):
        """Override unlink to update weekly business records when business KPI data is deleted"""
        # Store affected employee + date before deletion
        affected = [
            (rec.resource_user_id, rec.date_of_project)
            for rec in self
            if rec.resource_user_id and rec.date_of_project
        ]

        result = super(DailyProgressBusiness, self).unlink()

        for user, date in affected:
            employee = self.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
            if employee:
                self._update_single_weekly_business_record(employee, date)

        return result

    def _update_weekly_business_records(self, progress_records):
        """Update weekly business records for the given daily.progress.business records"""
        for progress in progress_records:
            if not progress.resource_user_id or not progress.date_of_project:
                continue

            employee = self.env['hr.employee'].search([
                ('user_id', '=', progress.resource_user_id.id)
            ], limit=1)

            if not employee:
                _logger.warning(f"No employee found for user {progress.resource_user_id.name}")
                continue

            self._update_single_weekly_business_record(employee, progress.date_of_project)

    def _update_single_weekly_business_record(self, employee, date):
        """Find the weekly business record for the given employee & date and recompute its KPI count"""
        WeeklyBusiness = self.env['employee.attendance.kpi.weekly.business']

        try:
            iso_year, iso_week, _ = date.isocalendar()

            weekly_record = WeeklyBusiness.search([
                ('employee_id', '=', employee.id),
                ('year', '=', iso_year),
                ('week_number_int', '=', iso_week),
            ], limit=1)

            if weekly_record:
                weekly_record._compute_kpi_count()
                _logger.debug(
                    f"Refreshed weekly business record for {employee.name} - Sprint_{iso_week} ({iso_year})"
                )
            else:
                # Auto-create the weekly record if it doesn't exist yet
                week_start, week_end = WeeklyBusiness.get_week_date_range(iso_year, iso_week)
                WeeklyBusiness.create({
                    'employee_id': employee.id,
                    'year': iso_year,
                    'week_number': f"Sprint_{iso_week}",
                    'week_number_int': iso_week,
                    'week_start_date': week_start,
                    'week_end_date': week_end,
                })
                _logger.info(
                    f"Auto-created weekly business record for {employee.name} - Sprint_{iso_week} ({iso_year})"
                )

        except Exception as e:
            _logger.error(
                f"Error updating weekly business record for {employee.name} on {date}: {str(e)}"
            )
