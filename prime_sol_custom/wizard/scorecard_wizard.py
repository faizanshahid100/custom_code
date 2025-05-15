from datetime import date, timedelta

from odoo import api, fields, models


class ScorecardWizard(models.TransientModel):
    _name = "scorecard.wizard"
    _description = 'Scorecard Wizard'

    @api.model
    def default_get(self, default_fields):
        res = super(ScorecardWizard, self).default_get(default_fields)
        today = date.today()

        # ✅ First day of the current year
        first_day_current_year = date(today.year, 1, 1)

        res.update({
            'date_from': first_day_current_year or False,
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

        month_diff = (self.date_to.year - self.date_from.year) * 12 + (self.date_to.month - self.date_from.month + 1)
        total_bonus_points = month_diff * 5

        employees = self.env['hr.employee'].search([]).filtered(lambda l: l.contractor.id == self.partner_id.id)
        for employee in employees:
            ####### Feedback ########
            feedback = 1

            feedbacks = employee.feedback_ids.filtered(
                lambda fb: self.date_from <= fb.date_feedback <= self.date_to
            )

            if feedbacks:
                negative_count = sum(1 for fb in feedbacks if fb.feedback_type == 'negative')
                total_negative_points = negative_count * 5
                points_of_tenure = total_bonus_points - total_negative_points

                feedback = min(points_of_tenure / total_bonus_points, 1) if total_bonus_points else 0

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
            daily_attendance = min((len(employee_attendance) + len(leave_days)) / len(work_days), 1) if work_days else 1

            ####### KPI ########
            applied_kpi = self.env['daily.progress'].search([
                ('resource_user_id.employee_id', '=', employee.id),
                ('date_of_project', '>=', self.date_from),
                ('date_of_project', '<=', self.date_to)
            ])

            kpi = min((len(applied_kpi) + len(leave_days)) / len(work_days), 1) if work_days else 0

            ####### Weekly Meetings ########
            meetings = self.env['meeting.tracker'].search([
                ('client_id', '=', self.partner_id.id),
                ('date', '>=', self.date_from),
                ('date', '<=', self.date_to)
            ])

            attended_meetings = meetings.meeting_details.filtered(lambda l: l.employee_id.id == employee.id)

            weekly_meetings = min(len(attended_meetings) / len(meetings), 1) if meetings else 1

            ####### Office On-Site ########
            # Some Values get from attendance above code chunk
            if work_days:
                onsite_count = len(employee_attendance.filtered(lambda l: l.is_onsite_in))
                total_days = len(work_days)

                if onsite_count == 0:
                    leave_days = []
                office_coming = min((onsite_count + len(leave_days)) / total_days, 1)
            else:
                office_coming = 1
            # Create the Records
            self.env['score.card'].create({
                'employee_id': employee.id,
                'partner_id': self.partner_id.id,
                'feedback': feedback,
                'kpi': kpi,
                'weekly_meeting': weekly_meetings,
                'daily_attendance': daily_attendance,
                'office_coming': office_coming,
            })

        return {
            'name': 'Score Card',
            'type': 'ir.actions.act_window',
            'res_model': 'score.card',
            'view_mode': 'tree',
            'target': 'current',
            'domain': [],
        }
