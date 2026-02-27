# -*- coding: utf-8 -*-
"""
Weekly Business KPI Tracker — Odoo 16
======================================
Tracks whether Business department employees (pss_group = non_technical)
have filed their weekly KPI in 'daily.progress.business'.

Key notes about daily.progress.business:
  - Links to employee via resource_user_id (res.users) -> employee_id
  - Files ONCE per week (not daily)
  - Has week_of_year (e.g. 'Week-9') and year_of_kpi fields

One record per employee per week, auto-generated every Monday.
Status: Filed / Not Filed
"""
from odoo import api, fields, models
from datetime import date, timedelta


class WeeklyBusinessKPI(models.Model):
    _name        = 'weekly.business.kpi'
    _description = 'Weekly Business KPI Tracker'
    _order       = 'week_start_date desc, employee_id'
    _rec_name    = 'display_name'

    # ── Identity ──────────────────────────────────────────────────────────────
    employee_id     = fields.Many2one(
        'hr.employee', string='Employee', required=True, index=True, ondelete='cascade'
    )
    department_id   = fields.Many2one(
        'hr.department', string='Department',
        related='employee_id.department_id', store=True, readonly=True
    )
    week_start_date = fields.Date(string='Week Start (Mon)', required=True)
    week_end_date   = fields.Date(string='Week End (Sun)', compute='_compute_dates', store=True)
    week_of_year    = fields.Char(string='Week #',         compute='_compute_dates', store=True)
    year_of_kpi     = fields.Char(string='KPI Year',       compute='_compute_dates', store=True)
    display_name    = fields.Char(compute='_compute_display_name', store=True)

    # ── KPI Filing Status ─────────────────────────────────────────────────────
    kpi_filed       = fields.Boolean(string='KPI Filed',   compute='_compute_kpi_filed', store=True)
    filed_date      = fields.Date   (string='Filed On',    compute='_compute_kpi_filed', store=True)
    filing_status   = fields.Selection([
        ('filed',     'Filed'),
        ('not_filed', 'Not Filed'),
    ], string='Status', compute='_compute_kpi_filed', store=True)
    business_kpi_id = fields.Many2one(
        'daily.progress.business', string='Business KPI Record',
        compute='_compute_kpi_filed', store=True, readonly=True
    )

    _sql_constraints = [
        ('unique_employee_week', 'UNIQUE(employee_id, week_start_date)',
         'A business KPI tracker record already exists for this employee and week.'),
    ]

    # =========================================================================
    # Computes
    # =========================================================================

    @api.depends('week_start_date')
    def _compute_dates(self):
        for rec in self:
            if rec.week_start_date:
                iso = rec.week_start_date.isocalendar()
                rec.week_end_date = rec.week_start_date + timedelta(days=6)
                rec.week_of_year  = 'Week-%s' % iso[1]
                rec.year_of_kpi   = str(iso[0])
            else:
                rec.week_end_date = False
                rec.week_of_year  = ''
                rec.year_of_kpi   = ''

    @api.depends('employee_id', 'week_of_year', 'year_of_kpi')
    def _compute_display_name(self):
        for rec in self:
            emp  = rec.employee_id.name or ''
            week = rec.week_of_year or ''
            year = rec.year_of_kpi  or ''
            rec.display_name = '%s — %s %s' % (emp, week, year)

    @api.depends('employee_id', 'week_start_date', 'week_end_date', 'week_of_year', 'year_of_kpi')
    def _compute_kpi_filed(self):
        DPB = self.env['daily.progress.business']
        for rec in self:
            if not rec.employee_id or not rec.week_start_date or not rec.week_of_year:
                rec.kpi_filed       = False
                rec.filed_date      = False
                rec.filing_status   = 'not_filed'
                rec.business_kpi_id = False
                continue

            # daily.progress.business links via resource_user_id (res.users)
            # employee -> user via employee_id.user_id
            user = rec.employee_id.user_id
            if not user:
                rec.kpi_filed       = False
                rec.filed_date      = False
                rec.filing_status   = 'not_filed'
                rec.business_kpi_id = False
                continue

            # Match by user + week_of_year + year_of_kpi
            # (business employees file once a week, not daily)
            record = DPB.search([
                ('resource_user_id', '=', user.id),
                ('week_of_year',     '=', rec.week_of_year),
                ('year_of_kpi',      '=', rec.year_of_kpi),
            ], limit=1, order='date_of_project asc')

            if record:
                rec.kpi_filed       = True
                rec.filed_date      = record.date_of_project
                rec.filing_status   = 'filed'
                rec.business_kpi_id = record.id
            else:
                rec.kpi_filed       = False
                rec.filed_date      = False
                rec.filing_status   = 'not_filed'
                rec.business_kpi_id = False

    # =========================================================================
    # Actions / Helpers
    # =========================================================================

    def action_refresh(self):
        """Manual refresh — re-check filing status."""
        self._compute_kpi_filed()
        return True

    def action_open_business_kpi(self):
        """Open the linked daily.progress.business record."""
        self.ensure_one()
        if not self.business_kpi_id:
            return
        return {
            'type':      'ir.actions.act_window',
            'res_model': 'daily.progress.business',
            'res_id':    self.business_kpi_id.id,
            'view_mode': 'form',
            'target':    'current',
        }

    @api.model
    def generate_for_week(self, week_start=None):
        """
        Auto-create WeeklyBusinessKPI tracker records for all active Business employees.
        Triggered by cron every Monday.
        """
        if not week_start:
            today = date.today()
            week_start = today - timedelta(days=today.weekday())

        employees = self.env['hr.employee'].search([
            ('active',             '=', True),
            ('department_id.name', 'ilike', 'Business'),
            ('pss_group',          '=', 'non_technical'),
        ])

        created = updated = 0
        for emp in employees:
            existing = self.search([
                ('employee_id',     '=', emp.id),
                ('week_start_date', '=', week_start),
            ], limit=1)
            if not existing:
                self.create({
                    'employee_id':     emp.id,
                    'week_start_date': week_start,
                })
                created += 1
            else:
                existing._compute_kpi_filed()
                updated += 1

        return {'created': created, 'updated': updated}
