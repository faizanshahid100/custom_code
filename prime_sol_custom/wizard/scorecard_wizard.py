from datetime import date, timedelta

from odoo import api, fields, models


class ScorecardWizard(models.TransientModel):
    _name = "scorecard.wizard"
    _description = 'Scorecard Wizard'

    @api.model
    def default_get(self, default_fields):
        res = super(ScorecardWizard, self).default_get(default_fields)
        today = date.today()

        # ✅ First day of the current month
        first_day_current_month = today.replace(day=1)

        # ✅ Yesterday (optional, not used here but you had it before)
        yesterday = today - timedelta(days=1)

        res.update({
            'date_from': first_day_current_month or False,
            'date_to': today or False
        })
        return res

    date_from = fields.Date(string="Start Date", required=True)
    date_to = fields.Date(string="End Date", required=True)
    partner_id = fields.Many2one('res.partner', string="Company", required=True, domain=[('is_company', '=', True)])

    def get_employee_leave_dates(self, employee, start_date, end_date):
        leave_records = self.env['hr.leave'].search([
            ('employee_id', '=', employee.id),
            ('state', '=', 'validate'),
            ('request_date_from', '>=', start_date),
            ('request_date_to', '<=', end_date),
        ])
        leave_dates = []
        for leave in leave_records:
            current_day = leave.request_date_from
            while current_day <= leave.request_date_to:
                leave_dates.append(current_day.day)
                current_day += timedelta(days=1)
        return leave_dates

    def get_employee_leave_dates(self, employee, start_date, end_date):
        leave_records = self.env['hr.leave'].search([
            ('employee_id', '=', employee.id),
            ('state', '=', 'validate'),
            ('request_date_from', '>=', start_date),
            ('request_date_to', '<=', end_date),
        ])
        leave_dates = []
        for leave in leave_records:
            current_day = leave.request_date_from
            while current_day <= leave.request_date_to:
                leave_dates.append(current_day.day)
                current_day += timedelta(days=1)
        return leave_dates

    def action_confirm(self):
        # Optional: Clear existing summaries
        self.env['score.card'].search([]).unlink()

        employees = self.env['hr.employee'].search([]).filtered(lambda l: l.contractor.id == self.partner_id.id)
        for employee in employees:
            survey = 0.00
            kpi = 0.00
            weekly_meeting = 0.00
            daily_attendance = 0.00
            office_coming = 0.00

            if employee.feedback_ids:
                relevant_feedback = employee.feedback_ids.filtered(
                    lambda l: self.date_from <= l.date_feedback <= self.date_to
                )
                total = len(relevant_feedback)

                if total > 0:
                    positive_or_neutral = len(relevant_feedback.filtered(lambda l: l.feedback_status != 'negative'))
                    survey = positive_or_neutral / total
                else:
                    survey = 0.0


            # Employee Present Days
            employee_attendance = self.env['hr.attendance'].search([('employee_id', '=', employee.id), ('check_in', '>=', self.date_from), ('check_in', '<=', self.date_to)])
            attendance_dates = employee_attendance.mapped('check_in')
            attendance_days = [dt.isoweekday() for dt in attendance_dates]

            # Total Working Days
            work_days = []
            if not employee.resource_calendar_id:
                raise ValueError("Employee has no working schedule assigned.")
            working_hours = employee.resource_calendar_id
            working_days = set(attendance.dayofweek for attendance in working_hours.attendance_ids)
            date_range = [
                (self.date_from + timedelta(days=i))
                for i in range((self.date_to - self.date_from).days + 1)
            ]
            for date in date_range:
                if str(date.weekday()) in working_days:
                    work_days.append(date.day)

            # Leave Days
            leave_days = self.get_employee_leave_dates(employee, self.date_from, self.date_to)

            # This value to pass in field
            daily_attendance =  (len(attendance_days)+len(leave_days))/len(work_days)

        # # Build search domain if filtering is needed
        # domain = []
        # if self.partner_id:
        #     # Add conditions for partner_id and date range
        #     domain.append(('meeting_id.client_id', '=', self.partner_id.id))
        #     domain.append(('meeting_id.date', '>=', self.date_from))
        #     domain.append(('meeting_id.date', '<=', self.date_to))
        #
        # details = self.env['meeting.details'].search(domain)
        #
        # # Initialize dictionaries to track meeting counts
        # employee_meeting_count = {}
        # employee_attended_count = {}
        #
        # # Iterate over the details to count total and attended meetings for each employee
        # for detail in details:
        #     employee_id = detail.employee_id.id
        #
        #     # Count total meetings
        #     if employee_id not in employee_meeting_count:
        #         employee_meeting_count[employee_id] = 0
        #     employee_meeting_count[employee_id] += 1
        #
        #     # Count attended meetings (where is_present is True)
        #     if detail.is_present:
        #         if employee_id not in employee_attended_count:
        #             employee_attended_count[employee_id] = 0
        #         employee_attended_count[employee_id] += 1
        #
        # # Initialize a set to track processed employee_ids
        # processed_employee_ids = set()
        #
        # for detail in details:
        #     employee_id = detail.employee_id.id
        #
        #     # Skip if the employee_id has already been processed
        #     if employee_id in processed_employee_ids:
        #         continue
        #
        #     # Add the employee_id to the set to avoid duplicates
        #     processed_employee_ids.add(employee_id)
        #
        #     # Get the total meetings and attended meetings counts for the employee
        #     total_meetings = employee_meeting_count.get(employee_id, 0)
        #     attended_meetings = employee_attended_count.get(employee_id, 0)
        #
        #     # Create a new summary entry with total and attended meetings count
        #     self.env['meeting.attendance.summary'].create({
        #         'employee_id': employee_id,
        #         'partner_id': detail.employee_id.contractor.id if detail.employee_id.contractor else '',
        #         'level': detail.employee_id.level if detail.employee_id.level else '',
        #         'kpi_measurement': detail.employee_id.kpi_measurement,
        #         'job_id': detail.employee_id.job_id.id if detail.employee_id.job_id else '',
        #         'total_meetings': total_meetings,  # Total meetings count
        #         'attended_meetings': attended_meetings,  # Attended meetings count
        #     })
        #
        # return {
        #     'name': 'Meeting Attendance Summary',
        #     'type': 'ir.actions.act_window',
        #     'res_model': 'meeting.attendance.summary',
        #     'view_mode': 'tree',
        #     'target': 'current',  # This makes it full-screen, not a popup
        #     'domain': [],  # Optional: you can pass specific domain if needed
        # }
