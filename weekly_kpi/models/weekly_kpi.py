# -*- coding: utf-8 -*-
"""
Weekly KPI Achievement — Odoo 16
=================================
Active targets = hr.employee fields > 0 among:
    ticket_resolved, CAST, avg_resolution_time, billable_hours
Weight/target = 100 / active_count
ticket_resolved uses SUM; all % fields use AVG over (KPI days + leave days)
Score/target = min((achieved / target) * weight, weight)
Total KPI Score = sum of all active target scores
"""
from odoo import api, fields, models
from odoo.exceptions import ValidationError
from datetime import date, timedelta


class WeeklyKPI(models.Model):
    _name        = 'weekly.kpi'
    _description = 'Weekly KPI Achievement'
    _order       = 'week_start_date desc, employee_id'
    _rec_name    = 'display_name'

    # ── Identity ──────────────────────────────────────────────────────────────
    employee_id     = fields.Many2one('hr.employee', string='Employee', required=True, index=True, ondelete='cascade')
    department_id   = fields.Many2one('hr.department', string='Department',
                                      related='employee_id.department_id', store=True, readonly=True)
    week_start_date = fields.Date(string='Week Start (Mon)', required=True)
    week_end_date   = fields.Date(string='Week End (Sun)',   compute='_compute_dates', store=True)
    week_of_year    = fields.Char(string='Week #',           compute='_compute_dates', store=True)
    year_of_kpi     = fields.Char(string='KPI Year',         compute='_compute_dates', store=True)
    display_name    = fields.Char(compute='_compute_display_name', store=True)
    manager_note    = fields.Char(string='Manager Note')

    # ── Weekly Targets (mirror from hr.employee) ───────────────────────────────
    target_ticket_resolved     = fields.Integer(related='employee_id.ticket_resolved',     store=True, readonly=True, string='Target: Tickets Resolved')
    target_cast                = fields.Integer(related='employee_id.CAST',                store=True, readonly=True, string='Target: Calls %')
    target_avg_resolution_time = fields.Float  (related='employee_id.avg_resolution_time', store=True, readonly=True, string='Target: Response Time %')
    target_billable_hours      = fields.Integer(related='employee_id.billable_hours',      store=True, readonly=True, string='Target: Billable Hours %')
    alert_tickets              = fields.Integer(related='employee_id.alert_tickets',       store=True, readonly=True, string='Alert Tickets')

    # ── Active target flags (kpi only) ────────────────────────────────────────
    active_ticket_resolved     = fields.Boolean(compute='_compute_active_targets', store=True)
    active_cast                = fields.Boolean(compute='_compute_active_targets', store=True)
    active_avg_resolution_time = fields.Boolean(compute='_compute_active_targets', store=True)
    active_billable_hours      = fields.Boolean(compute='_compute_active_targets', store=True)
    active_target_count        = fields.Integer(compute='_compute_active_targets', store=True, string='# Active Targets')
    weight_per_target          = fields.Float  (compute='_compute_active_targets', store=True, string='Weight / Target (%)', digits=(6, 4))

    # ── Weekly Achieved (aggregated from daily.progress) ──────────────────────
    achieved_ticket_resolved     = fields.Integer(compute='_compute_achieved', store=True, string='Achieved: Tickets Resolved')
    achieved_cast                = fields.Float  (compute='_compute_achieved', store=True, string='Achieved: Calls %')
    achieved_avg_resolution_time = fields.Integer(compute='_compute_achieved', store=True, string='Achieved: Avg Resolution Time')
    achieved_billable_hours      = fields.Float  (compute='_compute_achieved', store=True, string='Achieved: Avg Billable %')
    working_days_count           = fields.Integer(compute='_compute_achieved', store=True, string='Days Logged')

    # ── Per-target weighted scores ─────────────────────────────────────────────
    pct_ticket_resolved     = fields.Float(compute='_compute_scores', store=True, string='Score: Tickets (%)',       digits=(6, 2))
    pct_cast                = fields.Float(compute='_compute_scores', store=True, string='Score: Calls (%)',         digits=(6, 2))
    pct_avg_resolution_time = fields.Float(compute='_compute_scores', store=True, string='Score: Response Time (%)', digits=(6, 2))
    pct_billable_hours      = fields.Float(compute='_compute_scores', store=True, string='Score: Billable Hours (%)', digits=(6, 2))

    # ── Final ──────────────────────────────────────────────────────────────────
    total_kpi_score = fields.Float(compute='_compute_scores', store=True, string='Total KPI Score (%)', digits=(6, 2))
    kpi_grade       = fields.Char (compute='_compute_grade',  store=True, string='Grade')

    _sql_constraints = [
        ('unique_employee_week', 'UNIQUE(employee_id, week_start_date)',
         'A KPI record already exists for this employee and week.'),
    ]

    # =========================================================================
    # Compute Methods
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

    @api.depends(
        'target_ticket_resolved', 'target_cast',
        'target_avg_resolution_time', 'target_billable_hours',
    )
    def _compute_active_targets(self):
        for rec in self:
            t = rec.target_ticket_resolved     > 0
            c = rec.target_cast                > 0
            r = rec.target_avg_resolution_time > 0
            b = rec.target_billable_hours      > 0

            cnt = sum([t, c, r, b])
            rec.active_ticket_resolved     = t
            rec.active_cast                = c
            rec.active_avg_resolution_time = r
            rec.active_billable_hours      = b
            rec.active_target_count        = cnt
            rec.weight_per_target          = (100.0 / cnt) if cnt else 0.0

    def _get_leave_days_in_week(self, employee, week_start, week_end):
        """
        Count the number of APPROVED leave days for an employee within the week.
        Only counts days that fall within the employee's working schedule.
        """
        leaves = self.env['hr.leave'].search([
            ('employee_id', '=', employee.id),
            ('state',       '=', 'validate'),
            ('request_date_from', '<=', week_end),
            ('request_date_to',   '>=', week_start),
        ])

        leave_days = set()
        current = week_start
        while current <= week_end:
            for leave in leaves:
                if leave.request_date_from <= current <= leave.request_date_to:
                    leave_days.add(current)
                    break
            current += timedelta(days=1)

        # Only count days that are actual working days in employee's calendar
        calendar = employee.resource_calendar_id or employee.company_id.resource_calendar_id
        if calendar:
            working_weekdays = set(int(att.dayofweek) for att in calendar.attendance_ids)
            leave_days = {d for d in leave_days if d.weekday() in working_weekdays}

        return len(leave_days)

    @api.depends('employee_id', 'week_start_date', 'week_end_date')
    def _compute_achieved(self):
        DP = self.env['daily.progress']
        for rec in self:
            if not rec.employee_id or not rec.week_start_date or not rec.week_end_date:
                rec.achieved_ticket_resolved     = 0
                rec.achieved_cast                = 0.0
                rec.achieved_avg_resolution_time = 0
                rec.achieved_billable_hours      = 0.0
                rec.working_days_count           = 0
                continue

            records = DP.search([
                ('employee_id',    '=', rec.employee_id.id),
                ('date_of_project','>=', rec.week_start_date),
                ('date_of_project','<=', rec.week_end_date),
            ])

            kpi_days   = len(records)

            # Leave days in this week (approved, on working days, not already filed)
            filed_dates = set(records.mapped('date_of_project'))
            leave_days  = self._get_leave_days_in_week(
                rec.employee_id, rec.week_start_date, rec.week_end_date
            )
            # Avoid double-counting: if employee filed KPI on a leave day, don't add it twice
            # We count leave days that were NOT filed
            leave_days_not_filed = self._get_leave_days_in_week_excluding(
                rec.employee_id, rec.week_start_date, rec.week_end_date, filed_dates
            )

            # Denominator = KPI days filed + leave days not filed
            denominator = kpi_days + leave_days_not_filed

            rec.working_days_count           = denominator
            # ticket_resolved → SUM (total tickets resolved in the week vs weekly target)
            rec.achieved_ticket_resolved     = sum(records.mapped('avg_resolved_ticket'))
            # All % fields → AVG over (kpi_days + leave_days), leave days contribute 0 to sum
            cast_sum       = sum(records.mapped('no_calls_duration'))
            res_time_sum   = sum(records.mapped('avg_resolution_time'))
            billable_sum   = sum(records.mapped('billable_hours'))
            rec.achieved_cast                = round(cast_sum     / denominator, 2) if denominator > 0 else 0.0
            rec.achieved_avg_resolution_time = round(res_time_sum / denominator, 2) if denominator > 0 else 0.0
            rec.achieved_billable_hours      = round(billable_sum / denominator, 2) if denominator > 0 else 0.0

    def _get_leave_days_in_week_excluding(self, employee, week_start, week_end, exclude_dates):
        """
        Count approved leave days in the week, excluding dates already in exclude_dates.
        Only counts days within the employee's working schedule.
        """
        leaves = self.env['hr.leave'].search([
            ('employee_id',      '=', employee.id),
            ('state',            '=', 'validate'),
            ('request_date_from','<=', week_end),
            ('request_date_to',  '>=', week_start),
        ])

        leave_days = set()
        current = week_start
        while current <= week_end:
            if current not in exclude_dates:
                for leave in leaves:
                    if leave.request_date_from <= current <= leave.request_date_to:
                        leave_days.add(current)
                        break
            current += timedelta(days=1)

        # Only count actual working days
        calendar = employee.resource_calendar_id or employee.company_id.resource_calendar_id
        if calendar:
            working_weekdays = set(int(att.dayofweek) for att in calendar.attendance_ids)
            leave_days = {d for d in leave_days if d.weekday() in working_weekdays}

        return len(leave_days)

    @api.depends(
        'weight_per_target',
        'active_ticket_resolved', 'active_cast', 'active_avg_resolution_time', 'active_billable_hours',
        'target_ticket_resolved', 'target_cast', 'target_avg_resolution_time', 'target_billable_hours',
        'achieved_ticket_resolved', 'achieved_cast', 'achieved_avg_resolution_time', 'achieved_billable_hours',
    )
    def _compute_scores(self):
        for rec in self:
            w = rec.weight_per_target

            def _score(active, achieved, target):
                if not active or not target:
                    return 0.0
                return min((float(achieved) / float(target)) * w, w)

            rec.pct_ticket_resolved     = _score(rec.active_ticket_resolved,     rec.achieved_ticket_resolved,     rec.target_ticket_resolved)
            rec.pct_cast                = _score(rec.active_cast,                rec.achieved_cast,                rec.target_cast)
            rec.pct_avg_resolution_time = _score(rec.active_avg_resolution_time, rec.achieved_avg_resolution_time, rec.target_avg_resolution_time)
            rec.pct_billable_hours      = _score(rec.active_billable_hours,      rec.achieved_billable_hours,      rec.target_billable_hours)

            rec.total_kpi_score = (
                rec.pct_ticket_resolved +
                rec.pct_cast +
                rec.pct_avg_resolution_time +
                rec.pct_billable_hours
            )

    @api.depends('total_kpi_score')
    def _compute_grade(self):
        for rec in self:
            if rec.total_kpi_score == 100:
                rec.kpi_grade = 'Excellent'
            elif rec.total_kpi_score >= 90:
                rec.kpi_grade = 'Good'
            elif rec.total_kpi_score >= 80:
                rec.kpi_grade = 'Average'
            elif rec.total_kpi_score > 0:
                rec.kpi_grade = 'Below Target'
            else:
                rec.kpi_grade = 'No Targets Set'

    # =========================================================================
    # Actions / Helpers
    # =========================================================================

    def action_refresh(self):
        """Manual refresh — recomputes all scores for this record."""
        self._compute_achieved()
        self._compute_scores()
        self._compute_grade()
        return True

    @api.model
    def generate_for_week(self, week_start=None):
        """
        Auto-create WeeklyKPI records for all active employees.
        Triggered by cron every Monday, or call manually from shell.
        """
        if not week_start:
            today = date.today()
            week_start = today - timedelta(days=today.weekday())

        employees = self.env['hr.employee'].search([
            ('active', '=', True),
            ('department_id.name', 'ilike', 'Tech'),
            ('pss_group', '=', 'technical'),
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
                existing._compute_achieved()
                existing._compute_scores()
                existing._compute_grade()
                updated += 1

        return {'created': created, 'updated': updated}
