# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import datetime, date, time, timedelta
import pytz


class AttendanceDashboard(models.Model):
    _name = 'attendance.dashboard'
    _description = 'Employees missing check-in after duty start + 20 minutes'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    duty_start = fields.Datetime(string='Duty Start', required=True)
    threshold = fields.Datetime(string='Threshold', required=True)
    check_in = fields.Datetime(string='Check-In (first today)', readonly=True)
    minutes_overdue = fields.Char(string='Minutes Overdue', readonly=True)
    hours_overdue = fields.Integer(string='Hours Overdue', readonly=True)
    is_missing = fields.Boolean(string='Missing', default=False)

    @api.model
    def refresh(self):
        """Populate attendance.dashboard with employees missing check-in for today in PST (UTC+5)."""
        self.sudo().search([]).unlink()  # clear previous

        utc_now = datetime.now()
        today = fields.Date.today()

        employees = self.env['hr.employee'].sudo().search([('hour_start_from', '>', 0), ('department_id.name', 'in', ['Tech PK', 'Tech PH', 'Business PK', 'Business PH'])])

        for emp in employees:
            # 🔹 NEW: Skip employee if on approved leave today
            leave = self.env['hr.leave'].sudo().search([
                ('employee_id', '=', emp.id),
                ('state', '=', 'validate'),
                ('request_date_from', '<=', today),
                ('request_date_to', '>=', today),
            ], limit=1)
            # is today gazetted day
            gazetted_holidays = emp.sudo().gazetted_holiday_id.holiday_dates

            if leave or today.strftime("%d-%m-%Y") in gazetted_holidays:
                continue  # Skip — on leave
            # 🔹 NEW: Skip employee if today is their weekly off (based on resource calendar)
            calendar = emp.resource_calendar_id
            if calendar:
                # get weekday of today (0=Monday, 6=Sunday)
                weekday = today.weekday()
                working_intervals = calendar.attendance_ids.filtered(lambda att: int(att.dayofweek) == weekday)
                if not working_intervals:
                    continue  # Skip — no working hours today (off day)

            # convert float to hh:mm
            hour_float = float(emp.hour_start_from or 0.0)
            hours = int(hour_float)
            minutes = int(round((hour_float - hours) * 60))

            # duty start in PST (UTC+5)
            pst_today = utc_now + timedelta(hours=5)
            duty_time_pst = datetime.combine(pst_today.date(), time(hours, minutes))
            threshold_pst = duty_time_pst + timedelta(minutes=20)

            # back to UTC
            duty_time_utc = duty_time_pst - timedelta(hours=5)
            threshold_time_utc = threshold_pst - timedelta(hours=5)

            # if not yet passed the first threshold → skip
            if utc_now < threshold_time_utc:
                continue

            # attendance window per country
            if emp.country_id.name == 'Pakistan':
                checkin_domain = datetime.combine(utc_now.date(), time.min) - timedelta(hours=5)
            elif emp.country_id.name == 'Philippines':
                checkin_domain = datetime.combine(utc_now.date(), time.min) - timedelta(hours=8)
            else:
                checkin_domain = datetime.combine(utc_now.date(), time.min)

            attendance = self.env['hr.attendance'].sudo().search([
                ('employee_id', '=', emp.id),
                ('check_in', '>=', checkin_domain),
            ], order='check_in asc', limit=1)

            if attendance:
                continue  # already checked in

            # overdue calculation
            minutes_overdue = int((utc_now - threshold_time_utc).total_seconds() // 60)
                # ensure dashboard record
            self.sudo().create({
                'employee_id': emp.id,
                'duty_start': fields.Datetime.to_string(duty_time_utc),
                'threshold': fields.Datetime.to_string(threshold_time_utc),
                'check_in': False,
                'minutes_overdue': f"<div style='background-color: #ff0000; color: white; padding: 3px;text-align: center;border: 2px solid #000;'><b>{minutes_overdue}</b></div>" if minutes_overdue >= 60 else minutes_overdue,
                'hours_overdue': minutes_overdue // 60,
                'is_missing': True,
            })

            # prepare duty times in employee timezone
            utc_float = (emp.hour_start_from)
            tz_hours = int(utc_float)
            tz_minutes = int(round((utc_float - tz_hours) * 60))
            user_tz = emp.user_id.tz or "UTC"
            user_timezone = pytz.timezone(user_tz)

            utc_duty_time = datetime.combine(fields.Date.today(), time(tz_hours, tz_minutes))
            threshold_utc_duty_time = utc_duty_time + timedelta(minutes=20)

            duty_local = pytz.utc.localize(utc_duty_time).astimezone(user_timezone).strftime("%I:%M %p")
            threshold_local = pytz.utc.localize(threshold_utc_duty_time).astimezone(user_timezone).strftime("%I:%M %p")

            # employee reminder every 20 min overdue
            # if emp.work_email and minutes_overdue % 20 >= 1:
            if emp.work_email and minutes_overdue > 20 and minutes_overdue < 65 and minutes_overdue % 20 >= 1:
                mail_values = {
                    'subject': f"Reminder: Missing Check-in Alert for {emp.name}",
                    'body_html': f"""
                        <p>Dear {emp.name},</p>
                        <p>You still have not checked in for your duty today.</p>
                        <p><b>Duty Start Time:</b> {duty_local}<br/>
                           <b>Allowed Threshold:</b> {threshold_local}<br/>
                           <b>Minutes Overdue:</b> {minutes_overdue}</p>
                        <p>Please check in immediately.</p>
                    """,
                    'email_to': emp.work_email,
                }
                # self.env['mail.mail'].sudo().create(mail_values).send()

            # SDM group reminder every 60 min overdue
            # if minutes_overdue % 60 >= 1:
            if minutes_overdue > 60 and minutes_overdue < 126 and minutes_overdue % 60 >= 1:
                group = self.env.ref("prime_sol_custom.group_sdm", raise_if_not_found=False)
                if group and group.users:
                    group_emails = ",".join(u.email for u in group.users if u.email)
                    if group_emails:
                        mail_values = {
                            'subject': f"Escalation: {emp.name} Missing Check-in ({minutes_overdue} min overdue)",
                            'body_html': f"""
                                <p><b>Escalation Alert</b></p>
                                <p>Employee <b>{emp.name}</b> has not checked in for over {minutes_overdue} minutes.</p>
                                <p><b>Duty Start Time:</b> {duty_local}<br/>
                                   <b>Allowed Threshold:</b> {threshold_local}<br/>
                                   <b>Overdue:</b> {minutes_overdue} minutes</p>
                            """,
                            'email_to': group_emails,
                            'email_cc': emp.work_email or "",
                        }
                        # self.env['mail.mail'].sudo().create(mail_values).send()

        return True

    # @api.model
    # def refresh(self):
    #     """Populate attendance.dashboard with employees missing check-in for today in PST (UTC+5)."""
    #     self.sudo().search([]).unlink()  # clear previous
    #
    #     # current UTC time
    #     utc_now = datetime.now()
    #
    #     # get employees with defined duty start time
    #     employees = self.env['hr.employee'].sudo().search([('hour_start_from', '>', 0)])
    #
    #     for emp in employees:
    #         # convert float hours to hh:mm
    #         hour_float = float(emp.hour_start_from or 0.0)
    #         hours = int(hour_float)
    #         minutes = int(round((hour_float - hours) * 60))
    #
    #         # duty start in PST (UTC+5)
    #         pst_today = utc_now + timedelta(hours=5)
    #         duty_time_pst = datetime.combine(pst_today.date(), time(hours, minutes))
    #
    #         # threshold time in PST (20 min after duty start)
    #         threshold_pst = duty_time_pst + timedelta(minutes=20)
    #
    #         # convert duty + threshold back to UTC
    #         duty_time_utc = duty_time_pst - timedelta(hours=5)
    #         threshold_time_utc = threshold_pst - timedelta(hours=5)
    #
    #         # only check if threshold already passed
    #         if utc_now < threshold_time_utc:
    #             continue
    #
    #         # check if employee checked in anytime today
    #         if emp.country_id.name == 'Pakistan':
    #             checkin_domain = datetime.combine(utc_now.date(), time.min)-timedelta(hours=5)
    #         elif emp.country_id.name == 'Philippines':
    #             checkin_domain = datetime.combine(utc_now.date(), time.min)-timedelta(hours=8)
    #         else:
    #             checkin_domain = utc_now
    #
    #         attendance = self.env['hr.attendance'].sudo().search([
    #             ('employee_id', '=', emp.id),
    #             ('check_in', '>=', checkin_domain),
    #         ], order='check_in asc', limit=1)
    #
    #         if attendance:
    #             # already checked in (even if before duty time) → skip missing record
    #             continue
    #
    #         if not attendance:
    #             minutes_overdue = int((utc_now - threshold_time_utc).total_seconds() // 60)
    #
    #             # create dashboard entry
    #             self.sudo().create({
    #                 'employee_id': emp.id,
    #                 'duty_start': fields.Datetime.to_string(duty_time_utc),
    #                 'threshold': fields.Datetime.to_string(threshold_time_utc),
    #                 'check_in': False,
    #                 'minutes_overdue': minutes_overdue,
    #                 'hours_overdue': minutes_overdue // 60,
    #                 'is_missing': True,
    #             })
    #             # User's TimeZone
    #             utc_float = (emp.hour_start_from - 5)
    #             hours = int(utc_float)
    #             minutes = int(round((utc_float - hours) * 60))
    #
    #             user_tz = emp.user_id.tz or "UTC"   # Get user's timezone, default to 'UTC' if not set
    #             user_timezone = pytz.timezone(user_tz)
    #             utc_duty_time = datetime.combine(fields.Date.today(), time(hours, minutes))
    #             threshold_utc_duty_time = datetime.combine(fields.Date.today(), time(hours, minutes+20))
    #             current_time = pytz.utc.localize(utc_duty_time).astimezone(user_timezone).time()
    #             threshold_current_time = pytz.utc.localize(threshold_utc_duty_time).astimezone(user_timezone).time()
    #             formatted_current_time = current_time.strftime("%I:%M %p")
    #             threshold_formatted_current_time = threshold_current_time.strftime("%I:%M %p")
    #
    #
    #             # send email notification to employee
    #             if emp.work_email:
    #                 mail_values = {
    #                     'subject': f"Missing Check-in Alert: {emp.name}",
    #                     'body_html': f"""
    #                             <p>Dear {emp.name},</p>
    #                             <p>Our records show that you have not checked in for your duty today.</p>
    #                             <p><b>Duty Start Time:</b> {formatted_current_time}<br/>
    #                                <b>Allowed Threshold:</b> {threshold_formatted_current_time}<br/>
    #                                <b>Status:</b> Missing Check-in</p>
    #                             <p>Please ensure timely check-in.</p>
    #                         """,
    #                     'email_to': emp.work_email,
    #                 }
    #                 self.env['mail.mail'].sudo().create(mail_values).send()
    #
    #     return True

    def action_manual_refresh(self):
        """Button to refresh from UI for testing"""
        return self.env['attendance.dashboard'].refresh()
