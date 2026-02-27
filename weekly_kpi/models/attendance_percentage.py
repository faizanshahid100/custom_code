# -*- coding: utf-8 -*-
"""
Attendance Percentage — Odoo 16
=================================
Auto-generated every Monday for the PREVIOUS week.

Per employee per week:
  - working_days       = days in employee's calendar schedule for that week
  - attendance_count   = days employee actually checked in (hr.attendance)
  - time_off_count     = approved leave days that week (hr.leave validated)
  - total_present      = attendance_count + time_off_count
  - attendance_pct     = (total_present / working_days) * 100
"""
from odoo import api, fields, models
from datetime import date, timedelta


class AttendancePercentage(models.Model):
    _name        = 'attendance.percentage'
    _description = 'Weekly Attendance Percentage'
    _order       = 'week_start_date desc, employee_id'
    _rec_name    = 'display_name'

    # ── Compulsory Identity Fields ─────────────────────────────────────────────
    employee_id   = fields.Many2one(
        'hr.employee', string='Employee', required=True, index=True, ondelete='cascade'
    )
    department_id = fields.Many2one(
        'hr.department', string='Department',
        related='employee_id.department_id', store=True, readonly=True
    )
    country_id    = fields.Many2one(
        'res.country', string='Country',
        related='employee_id.country_id', store=True, readonly=True
    )

    # ── Week ──────────────────────────────────────────────────────────────────
    week_start_date = fields.Date(string='Week Start (Mon)', required=True)
    week_end_date   = fields.Date(string='Week End (Sun)', compute='_compute_dates', store=True)
    week_of_year    = fields.Char(string='Week #',          compute='_compute_dates', store=True)
    year            = fields.Char(string='Year',            compute='_compute_dates', store=True)
    display_name    = fields.Char(compute='_compute_display_name', store=True)

    # ── Core Attendance Fields (all auto-computed) ─────────────────────────────
    working_days      = fields.Integer(
        string='Working Days',
        compute='_compute_attendance_data', store=True,
        help='Number of scheduled working days in the week per employee calendar'
    )
    attendance_count  = fields.Integer(
        string='Attendance Count',
        compute='_compute_attendance_data', store=True,
        help='Number of distinct days employee checked in via hr.attendance'
    )
    first_check_in    = fields.Char(
        string='First Check-In (Mon)',
        compute='_compute_attendance_data', store=True,
        help='First check-in time on Monday of that week (HH:MM)'
    )
    time_off_count    = fields.Integer(
        string='Time-Off Count',
        compute='_compute_attendance_data', store=True,
        help='Number of approved leave days in the week'
    )
    total_present     = fields.Integer(
        string='Total (Att. + Time-Off)',
        compute='_compute_attendance_data', store=True,
        help='attendance_count + time_off_count'
    )
    attendance_pct    = fields.Float(
        string='Attendance %',
        compute='_compute_attendance_data', store=True,
        digits=(6, 2),
        help='(attendance_count + time_off_count) / working_days * 100'
    )
    status            = fields.Selection([
        ('full',    'Full'),
        ('partial', 'Partial'),
        ('absent',  'Absent'),
        ('no_data', 'No Data'),
    ], string='Status', compute='_compute_attendance_data', store=True)

    _sql_constraints = [
        ('unique_employee_week', 'UNIQUE(employee_id, week_start_date)',
         'An attendance record already exists for this employee and week.'),
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
                rec.year          = str(iso[0])
            else:
                rec.week_end_date = False
                rec.week_of_year  = ''
                rec.year          = ''

    @api.depends('employee_id', 'week_of_year', 'year')
    def _compute_display_name(self):
        for rec in self:
            emp  = rec.employee_id.name or ''
            week = rec.week_of_year or ''
            year = rec.year or ''
            rec.display_name = '%s — %s %s' % (emp, week, year)

    @api.depends('employee_id', 'week_start_date', 'week_end_date')
    def _compute_attendance_data(self):
        Attendance = self.env['hr.attendance']
        Leave      = self.env['hr.leave']

        for rec in self:
            if not rec.employee_id or not rec.week_start_date or not rec.week_end_date:
                rec._set_zero()
                continue

            emp        = rec.employee_id
            week_start = rec.week_start_date
            week_end   = rec.week_end_date

            # ── 1. Working Days ────────────────────────────────────────────────
            calendar = emp.resource_calendar_id or emp.company_id.resource_calendar_id
            working_weekdays = set()
            if calendar:
                working_weekdays = set(int(a.dayofweek) for a in calendar.attendance_ids)

            working_days = 0
            day = week_start
            while day <= week_end:
                if day.weekday() in working_weekdays:
                    working_days += 1
                day += timedelta(days=1)

            rec.working_days = working_days

            if working_days == 0:
                rec._set_zero()
                continue

            # ── 2. Attendance Count (distinct days checked in) ─────────────────
            # hr.attendance stores check_in as UTC datetime
            # We compare by date in employee's timezone if available, else use date_of_project
            att_records = Attendance.search([
                ('employee_id', '=', emp.id),
                ('check_in',    '>=', '%s 00:00:00' % week_start),
                ('check_in',    '<=', '%s 23:59:59' % week_end),
            ])

            # Distinct days
            att_days = set()
            first_checkin_monday = False
            for att in att_records:
                att_date = att.check_in.date()
                if week_start <= att_date <= week_end:
                    att_days.add(att_date)
                    # Capture first check-in on Monday of this week
                    if att_date == week_start and not first_checkin_monday:
                        first_checkin_monday = att.check_in.strftime('%H:%M')

            rec.attendance_count = len(att_days)
            rec.first_check_in   = first_checkin_monday or ''

            # ── 3. Time-Off Count (approved leaves, working days only) ─────────
            leaves = Leave.search([
                ('employee_id',      '=', emp.id),
                ('state',            '=', 'validate'),
                ('request_date_from','<=', week_end),
                ('request_date_to',  '>=', week_start),
            ])

            leave_days = set()
            day = week_start
            while day <= week_end:
                if day.weekday() in working_weekdays:
                    for leave in leaves:
                        if leave.request_date_from <= day <= leave.request_date_to:
                            leave_days.add(day)
                            break
                day += timedelta(days=1)

            # Don't double-count days already in attendance
            leave_days = leave_days - att_days
            rec.time_off_count = len(leave_days)

            # ── 4. Total & Percentage ─────────────────────────────────────────
            total = rec.attendance_count + rec.time_off_count
            rec.total_present  = total
            rec.attendance_pct = round((total / working_days) * 100, 2)

            # ── 5. Status ────────────────────────────────────────────────────
            if rec.attendance_pct >= 100:
                rec.status = 'full'
            elif rec.attendance_pct > 0:
                rec.status = 'partial'
            elif rec.attendance_pct == 0 and working_days > 0:
                rec.status = 'absent'
            else:
                rec.status = 'no_data'

    def _set_zero(self):
        self.working_days     = 0
        self.attendance_count = 0
        self.first_check_in   = ''
        self.time_off_count   = 0
        self.total_present    = 0
        self.attendance_pct   = 0.0
        self.status           = 'no_data'

    # =========================================================================
    # Actions / Helpers
    # =========================================================================

    def action_refresh(self):
        """Manual refresh button."""
        self._compute_attendance_data()
        return True

    @api.model
    def generate_last_week(self):
        """
        Auto-create AttendancePercentage records for ALL active employees
        for the PREVIOUS week. Called by cron every Monday.
        """
        today      = date.today()
        # Last Monday
        week_start = today - timedelta(days=today.weekday() + 7)
        week_end   = week_start + timedelta(days=6)

        employees = self.env['hr.employee'].search([('active', '=', True)])

        created = updated = 0
        for emp in employees:
            # Skip employees with no country (compulsory) — warn in log
            if not emp.country_id:
                continue

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
                existing._compute_attendance_data()
                updated += 1

        return {'created': created, 'updated': updated, 'week': str(week_start)}
