from datetime import date, timedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError


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
    department_id = fields.Many2one('hr.department', string='Department', required=True)

    def get_employee_leave_dates(self, employee, start_date, end_date):
        leave_records = self.env['hr.leave'].search([
            ('employee_id', '=', employee.id),
            ('state', '=', 'validate'),
            ('request_date_from', '<=', end_date),
            ('request_date_to', '>=', start_date),
        ])
        leave_dates = []

        # Get the set of weekend weekdays (e.g., [5, 6] for Saturday, Sunday)
        weekend_days = self.get_weekend_days(employee)

        for leave in leave_records:
            current_day = leave.request_date_from
            while current_day <= leave.request_date_to:
                if current_day.weekday() not in weekend_days:
                    leave_dates.append(current_day.day)
                current_day += timedelta(days=1)
        return leave_dates

    def get_weekend_days(self, employee):
        """Returns a list of weekday numbers (0=Monday, 6=Sunday) that are weekends for the employee."""
        calendar = employee.resource_calendar_id
        if not calendar:
            # Default to Saturday and Sunday
            return [5, 6]

        work_days = set()
        for attendance in calendar.attendance_ids:
            work_days.add(int(attendance.dayofweek))
        return [i for i in range(7) if i not in work_days]

    def action_confirm(self):
        # Optional: Clear existing summaries
        self.env['score.card'].search([]).unlink()

        month_diff = (self.date_to.year - self.date_from.year) * 12 + (self.date_to.month - self.date_from.month + 1)
        total_bonus_points = month_diff * 5

        employees = self.env['hr.employee'].search([]).filtered(
            lambda l: l.contractor.id == self.partner_id.id and l.department_id.id == self.department_id.id)
        if not employees:
            raise ValidationError('No employee record exist.')
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

            ####### Survey (Inprogress)########
            start = fields.Datetime.to_datetime(self.date_from)
            end = fields.Datetime.to_datetime(self.date_to) + timedelta(days=1, seconds=-1)

            survey_results = self.env['survey.user_input'].search([
                ('state', '=', 'done'),
                ('test_entry', '=', False),
                ('employee_id', '=', employee.id),
                ('survey_id.is_client_feedback', '=', True),
                ('create_date', '>=', start),
                ('create_date', '<=', end),
            ])
            survey_avg = []
            for result in survey_results:
                suggested_values = result.user_input_line_ids.filtered(
                    lambda l: l.answer_type == 'suggestion'
                ).suggested_answer_id.mapped('value')

                # Extract numeric values only and calculate average
                numeric_values = [int(v) for v in suggested_values if str(v).isdigit()]
                average = sum(numeric_values) / (len(numeric_values) * 5) if numeric_values else 0
                survey_avg.append(average)
            if len(survey_avg):
                survey = sum(survey_avg) / len(survey_avg)
            else:
                survey = 1
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
            if len(employee_attendance) == 0:
                daily_attendance = 0
            else:
                daily_attendance = min((len(employee_attendance) + len(leave_days)) / len(work_days),
                                       1) if work_days else 1

            ####### KPI ########
            progress_records = self.env['daily.progress'].search([
                ('resource_user_id.employee_id', '=', employee.id),
                ('date_of_project', '>=', self.date_from),
                ('date_of_project', '<=', self.date_to)
            ])
            if employee.kpi_measurement == 'kpi':
                total_kpi = len(work_days) * employee.d_ticket_resolved
                applied_kpi = sum(progress_records.mapped('avg_resolved_ticket'))
                if applied_kpi == 0:
                    kpi = 0
                else:
                    kpi = min((applied_kpi + (len(leave_days) * employee.d_ticket_resolved)) / total_kpi,
                              1) if total_kpi else 0
            elif employee.kpi_measurement == 'billable':
                total_billable = len(work_days) * employee.d_billable_hours
                applied_billable = sum(progress_records.mapped('billable_hours'))
                if applied_billable == 0:
                    kpi = 0
                else:
                    kpi = min((applied_billable + (len(leave_days) * employee.d_billable_hours)) / total_billable,
                              1) if total_billable else 0
            else:
                kpi = 1

            ####### Weekly Meetings ########
            meetings = self.env['meeting.tracker'].search([
                ('client_id', '=', self.partner_id.id),
                ('department_id', '=', self.department_id.id),
                ('date', '>=', self.date_from),
                ('date', '<=', self.date_to)
            ])

            attended_meetings = meetings.meeting_details.filtered(
                lambda l: l.employee_id.id == employee.id and l.is_present)

            weekly_meetings = min(len(attended_meetings) / len(meetings), 1) if meetings else 1
            ####### Office On-Site ########
            # Some Values get from attendance above code chunk
            if work_days:
                onsite_count = len(employee_attendance.filtered(lambda l: l.is_onsite_in))
                total_days = len(work_days)

                if onsite_count == 0:
                    office_coming = 0
                else:
                    office_coming = min((onsite_count + len(leave_days)) / total_days, 1)
            else:
                office_coming = 1
            # Create the Records
            self.env['score.card'].create({
                'employee_id': employee.id,
                'partner_id': self.partner_id.id,
                'department_id': self.department_id.id,
                'feedback': feedback,
                'survey': survey,
                'kpi': kpi,
                'weekly_meeting': weekly_meetings,
                'daily_attendance': daily_attendance,
                'office_coming': office_coming,
            })

        return {
            'name': 'Score Card',
            'type': 'ir.actions.act_window',
            'res_model': 'score.card',
            'view_mode': 'tree,pivot',
            'target': 'current',
            'domain': [],
        }
