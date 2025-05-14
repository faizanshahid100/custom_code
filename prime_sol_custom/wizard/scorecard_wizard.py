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
            ####### Feedback ########
            if employee.feedback_ids:
                relevant_feedback = employee.feedback_ids.filtered(
                    lambda l: self.date_from <= l.date_feedback <= self.date_to
                )
                total = len(relevant_feedback)

                if total > 0:
                    positive_feedback = len(relevant_feedback.filtered(lambda l: l.feedback_type != 'negative'))
                    feedback = positive_feedback / total
                else:
                    feedback = 1

            ####### Attendance ########
            # Employee Present Days
            employee_attendance = self.env['hr.attendance'].search(
                [('employee_id', '=', employee.id), ('check_in', '>=', self.date_from),
                 ('check_in', '<=', self.date_to)])
            # Leave Days
            leave_days = self.get_employee_leave_dates(employee, self.date_from, self.date_to)

            # Total Working Days
            work_days = []
            if not employee.resource_calendar_id:
                raise ValueError(f"Employee {employee.name} has no working schedule assigned.")

            working_hours = employee.resource_calendar_id
            working_days = set(attendance.dayofweek for attendance in working_hours.attendance_ids)
            date_range = [
                (self.date_from + timedelta(days=i))
                for i in range((self.date_to - self.date_from).days + 1)
            ]
            for date in date_range:
                if str(date.weekday()) in working_days:
                    work_days.append(date.day)

            # This value to pass in field
            daily_attendance = (len(employee_attendance) + len(leave_days)) / len(work_days)

            ####### KPI ########
            applied_kpi = self.env['daily.progress'].search([
                ('resource_user_id.employee_id', '=', employee.id),
                ('date_of_project', '>=', self.date_from),
                ('date_of_project', '<=', self.date_to)
            ])

            if work_days:
                kpi = len(applied_kpi) / len(work_days)
            else:
                kpi = 0

            ####### Weekly Meetings ########
            meetings = self.env['meeting.tracker'].search([
                ('client_id', '=', self.partner_id.id),
                ('date', '>=', self.date_from),
                ('date', '<=', self.date_to)
            ])

            attended_meetings = meetings.meeting_details.filtered(lambda l: l.employee_id.id == employee.id)

            # Handle ZeroDivisionError
            if meetings:
                weekly_meetings = len(attended_meetings) / len(meetings)
            else:
                weekly_meetings = 1

            # Create the Records
            self.env['score.card'].create({
                'employee_id': employee.id,
                'partner_id': self.partner_id.id,
                'feedback': feedback,
                'kpi': kpi,
                'weekly_meeting': weekly_meetings,
                'daily_attendance': daily_attendance,
                'office_coming': daily_attendance,
            })

        return {
            'name': 'Score Card',
            'type': 'ir.actions.act_window',
            'res_model': 'score.card',
            'view_mode': 'tree',
            'target': 'current',
            'domain': [],
        }
