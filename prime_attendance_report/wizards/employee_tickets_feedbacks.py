from odoo import api, fields, models, registry, _
from dateutil.relativedelta import relativedelta
import datetime
import io
from odoo.exceptions import ValidationError
import base64
from datetime import timedelta
import xlsxwriter
from collections import defaultdict


class EmployeeTicketsFeedback(models.TransientModel):
    _name = "employee.tickets.feedbacks"
    _description = 'Employee Tickets Feedbacks'

    @api.model
    def default_get(self, default_fields):
        res = super(EmployeeTicketsFeedback, self).default_get(default_fields)
        today = datetime.date.today()

        first_day_current_month = today.replace(day=1)  # 1st day of the current month
        yesterday = today - datetime.timedelta(days=1)  # Yesterday (today - 1 day)

        res.update({
            'start_date': first_day_current_month or False,
            'end_date': yesterday or False
        })
        return res

    start_date = fields.Date('Start Date', required=True)
    end_date = fields.Date('End Date', required=True)
    department_id = fields.Many2one('hr.department', string='Department', domain=[
        ('name', 'in', ('Tech PH', 'Tech PK', 'Business PH', 'Business PK', 'Business SA'))])
    period = fields.Selection([
        ('q1', 'Q1 (Jan - Mar)'),
        ('q2', 'Q2 (Apr - Jun)'),
        ('q3', 'Q3 (Jul - Sep)'),
        ('q4', 'Q4 (Oct - Dec)'),
        ('bi_annual', 'Bi-Annual'),
        ('annual', 'Annual'),
    ], string="Time Period")

    @api.onchange('period')
    def _onchange_period(self):
        """ Set start_date and end_date based on the selected period """
        if self.period:
            year = datetime.date.today().year
            if self.period == 'q1':
                self.start_date = datetime.date(year, 1, 1)
                self.end_date = datetime.date(year, 3, 31)
            elif self.period == 'q2':
                self.start_date = datetime.date(year, 4, 1)
                self.end_date = datetime.date(year, 6, 30)
            elif self.period == 'q3':
                self.start_date = datetime.date(year, 7, 1)
                self.end_date = datetime.date(year, 9, 30)
            elif self.period == 'q4':
                self.start_date = datetime.date(year, 10, 1)
                self.end_date = datetime.date(year, 12, 31)
            elif self.period == 'bi_annual':
                self.start_date = datetime.date(year, 1, 1)
                self.end_date = datetime.date(year, 6, 30)
            elif self.period == 'annual':
                self.start_date = datetime.date(year, 1, 1)
                self.end_date = datetime.date(year, 12, 31)

    # def get_sprint_of_year(self, date_value):
    #     return date_value.isocalendar().week

    def action_confirm_tickets(self):
        if self.department_id:
            employees = self.env['hr.employee'].sudo().search([('department_id', '=', self.department_id.id)])
        else:
            employees = self.env['hr.employee'].sudo().search([
                ('department_id.name', 'in', ('Tech PH', 'Tech PK', 'Business PH', 'Business PK', 'Business SA'))
            ])

        def get_week_ranges(start_date, end_date):
            ranges = []
            current = start_date
            while current <= end_date:
                week_end = current + timedelta(days=6 - current.weekday())
                if week_end > end_date:
                    week_end = end_date
                ranges.append((current, week_end))
                current = week_end + timedelta(days=1)
            return ranges

        def get_leave_days_in_week(employee, week_start, week_end, leaves):
            """Get number of approved leave days in the week and check if entire week is on leave"""
            # Get employee's working days for the week
            calendar = employee.resource_calendar_id or employee.company_id.resource_calendar_id
            if not calendar:
                return 0, False

            working_days = []
            current_date = week_start
            while current_date <= week_end:
                weekday = str(current_date.weekday())
                has_work = any(str(int(att.dayofweek)) == weekday or str(att.dayofweek) == weekday
                               for att in calendar.attendance_ids)
                if has_work:
                    working_days.append(current_date)
                current_date += timedelta(days=1)

            if not working_days:
                return 0, False

            # Count leave days and check if all working days are covered
            leave_days = 0
            for work_day in working_days:
                if any(leave.request_date_from <= work_day <= leave.request_date_to
                       for leave in leaves if leave.employee_id.id == employee.id):
                    leave_days += 1

            entire_week_on_leave = leave_days == len(working_days)
            return leave_days, entire_week_on_leave

        # Start from first coming Monday
        self.start_date = self.start_date + timedelta(days=(7 - self.start_date.weekday()) % 7)
        week_ranges = get_week_ranges(self.start_date, self.end_date)

        if len(week_ranges) > 26:
            raise ValidationError('You can not see tickets more than 26 weeks(6 months)')

        progresses = self.env['daily.progress'].sudo().search([
            ('date_of_project', '>=', self.start_date),
            ('date_of_project', '<=', self.end_date),
            ('resource_user_id.employee_id', 'in', employees.ids)
        ])

        # Get approved leaves for the date range
        leaves = self.env['hr.leave'].sudo().search([
            ('state', '=', 'validate'),
            ('employee_id', 'in', employees.ids),
            ('request_date_from', '<=', self.end_date),
            ('request_date_to', '>=', self.start_date)
        ])

        progress_map = defaultdict(lambda: defaultdict(int))
        comments_map = defaultdict(list)

        for progress in progresses:
            emp_id = progress.resource_user_id.employee_id.id
            if progress.manager_comment:
                comments_map[emp_id].append(progress.manager_comment.strip())

            for index, (start, end) in enumerate(week_ranges):
                if start <= progress.date_of_project <= end:
                    if progress.resource_user_id.employee_id.kpi_measurement == 'kpi':
                        progress_map[emp_id][index + 1] += progress.avg_resolved_ticket
                        break
                    elif progress.resource_user_id.employee_id.kpi_measurement == 'billable':
                        progress_map[emp_id][index + 1] += progress.billable_hours
                        break

        self.env['weekly.ticket.report'].sudo().search([]).unlink()

        # Create records in weekly.ticket.report
        for employee in employees:
            # ✅ Adjust start date if before employee joining date
            effective_start_date = max(self.start_date, employee.joining_date or self.start_date)
            effective_week_ranges = [r for r in week_ranges if r[1] >= effective_start_date]

            weekly_tickets = employee.d_ticket_resolved * 5 if employee.working_hours_type == 'peak' else 3
            vals = {
                'employee_id': employee.id,
                'employment_type': employee.employment_type,
                'working_hours_type': employee.working_hours_type,
            }

            resolved_tickets_total = 0
            all_tickets_total = 0
            completed_billable_hours = 0
            all_billable_hours = 0
            total_percent = 0
            last_week_index = len(effective_week_ranges)

            for week_index, (start, end) in enumerate(effective_week_ranges, start=1):
                # Check leave days in this week
                leave_days, entire_week_on_leave = get_leave_days_in_week(employee, start, end, leaves)

                # If entire week is on leave, show "Leave"
                if entire_week_on_leave:
                    vals[f'week_{week_index}'] = (
                        f"<div style='background-color: #e6f3ff; color: #0066cc; padding: 3px; text-align: center; font-weight: bold;'>"
                        f"Leave</div>"
                    )
                    continue

                current_value = progress_map[employee.id].get(week_index, 0)

                if employee.kpi_measurement == 'kpi':
                    # Adjust weekly target based on leave days
                    adjusted_weekly_tickets = weekly_tickets - (leave_days * (weekly_tickets / 5))
                    adjusted_weekly_tickets = max(0, int(adjusted_weekly_tickets))  # Ensure non-negative

                    resolved_tickets_total += current_value
                    all_tickets_total += adjusted_weekly_tickets

                    # --- Color logic ---
                    if week_index == last_week_index:
                        if current_value == 0:
                            color = "#ff0000"  # red
                            text_color = "white"
                        elif current_value >= adjusted_weekly_tickets:
                            color = "#c6efce"  # green
                            text_color = "black"
                        else:
                            color = "#ffff99"  # yellow
                            text_color = "black"
                    else:
                        if current_value >= adjusted_weekly_tickets:
                            color = "#c6efce"
                            text_color = "black"
                        else:
                            color = "#ff0000"
                            text_color = "white"

                    vals[f'week_{week_index}'] = (
                        f"<div style='background-color: {color}; color: {text_color}; padding: 3px;text-align: center;'>"
                        f"{current_value} / {adjusted_weekly_tickets}</div>"
                    )
                    # below is for Total Counts (The last Column)
                    vals['week_total'] = (
                        f"<div style='background-color: #c6efce; padding: 3px;text-align: center;border: 2px solid #000;'><b>{resolved_tickets_total} / {all_tickets_total}</b></div>"
                        if resolved_tickets_total >= all_tickets_total else
                        f"<div style='background-color: #ff0000; color: white; padding: 3px;text-align: center;border: 2px solid #000;'><b>{resolved_tickets_total} / {all_tickets_total}</b></div>"
                    )
                elif employee.kpi_measurement == 'billable':
                    weekly_target_hours = 100
                    # weekly_target_hours = employee.d_billable_hours or 0
                    achieved_percent = 0

                    # Avoid divide by zero
                    if weekly_target_hours > 0:
                        achieved_percent = (current_value / (weekly_target_hours * 5)) * 100

                    # Color logic (>= 50% green else red)
                    # --- Color logic ---
                    if week_index == last_week_index:
                        if achieved_percent == 0:
                            color = "#ff0000"  # red
                            text_color = "white"
                        elif achieved_percent >= 50:
                            color = "#c6efce"  # green
                            text_color = "black"
                        else:
                            color = "#ffff99"  # yellow
                            text_color = "black"
                    else:
                        if achieved_percent >= 50:
                            color = "#c6efce"
                            text_color = "black"
                        else:
                            color = "#ff0000"
                            text_color = "white"

                    # Display with percentage
                    vals[f'week_{week_index}'] = (
                        f"<div style='background-color: {color}; color: {text_color}; padding: 3px;text-align: center;'>"
                        f"{achieved_percent:.1f}%</div>"
                    )

                    # --- Total Section ---
                    completed_billable_hours += current_value
                    all_billable_hours += weekly_target_hours

                    if all_billable_hours > 0:
                        employee.name
                        total_percent = (completed_billable_hours / (all_billable_hours * 5)) * 100

                    vals['week_total'] = (
                        f"<div style='background-color: #c6efce; padding: 3px;text-align: center;border: 2px solid #000;'><b>{total_percent:.1f}%</b></div>" if total_percent >= 50 else f"<div style='background-color: #ff0000; color: white; padding: 3px;text-align: center;border: 2px solid #000;'><b>{total_percent:.1f}%</b></div>"
                    )
                else:
                    vals[f'week_{week_index}'] = (
                        f"<div style='padding: 3px;text-align: center;'>{current_value}</div>"
                    )

            # ✅ Combine all comments for this employee
            combined_comments = "\n".join(comments_map[employee.id]) if comments_map[employee.id] else ""
            vals['comments'] = combined_comments

            self.env['weekly.ticket.report'].sudo().create(vals)

        return {
            'name': f"Weekly Tickets Report ({self.start_date.strftime('%d-%b-%Y')} - {self.end_date.strftime('%d-%b-%Y')})",
            'type': 'ir.actions.act_window',
            'res_model': 'weekly.ticket.report',
            'view_mode': 'tree',
            'target': 'current',
        }

    def action_confirm_feedbacks(self):
        if self.department_id:
            employees = self.env['hr.employee'].sudo().search([('department_id', '=', self.department_id.id)])
        else:
            employees = self.env['hr.employee'].sudo().search(
                [('department_id.name', 'in', ('Tech PH', 'Tech PK', 'Business PH', 'Business PK', 'Business SA'))])

        def get_week_ranges(start_date, end_date):
            ranges = []
            current = start_date
            while current <= end_date:
                week_end = current + timedelta(days=6 - current.weekday())
                if week_end > end_date:
                    week_end = end_date
                ranges.append((current, week_end))
                current = week_end + timedelta(days=1)
            return ranges

        week_ranges = get_week_ranges(self.start_date, self.end_date)
        if len(week_ranges) > 26:
            raise ValidationError('You can not see tickets more than 26 weeks(6 months)')

        feedbacks = self.env['hr.employee.feedback'].sudo().search([
            ('employee_id', 'in', employees.ids),
            ('date_feedback', '>=', self.start_date),
            ('date_feedback', '<=', self.end_date)
        ])

        feedback_map = defaultdict(lambda: defaultdict(lambda: {'positive': 0, 'negative': 0}))
        for fb in feedbacks:
            emp_id = fb.employee_id.id
            for idx, (start, end) in enumerate(week_ranges):
                if start <= fb.date_feedback <= end:
                    feedback_map[emp_id][idx + 1][fb.feedback_type] += 1
                    break

        self.env['weekly.feedback.report'].sudo().search([]).unlink()

        for emp in employees:
            vals = {
                'employee_id': emp.id,
            }
            pos_total = 0
            neg_total = 0
            for i in range(1, 27):  # up to 26 weeks
                pos = feedback_map[emp.id][i]['positive']
                neg = feedback_map[emp.id][i]['negative']
                pos_total += pos
                neg_total += neg
                if pos or neg:
                    left_style = "background-color:#c6efce;" if pos > 0 else ""
                    right_style = "background-color:#ff0000; color:white;" if neg > 0 else ""
                    vals[f'week_{i}'] = f"""
                        <div style='width:100%; border:1px solid #000; text-align:center; font-weight:bold; font-size:12px;'>
                            <div style='width:50%; float:left; {left_style} padding:5px 0;'>{pos}</div>
                            <div style='width:50%; float:right; {right_style} padding:5px 0;'>{neg}</div>
                            <div style='clear:both;'></div>
                        </div>
                    """
                else:
                    vals[f'week_{i}'] = f"<div style='text-align:center; border:1px solid #000;padding:10px;'></div>"

                # Week total block with conditional background
                left_style_total = "background-color:#c6efce;" if pos_total > 0 else ""
                right_style_total = "background-color:#ff0000; color:white;" if neg_total > 0 else ""

                vals['week_total'] = f"""
                    <div style='width:100%; border:1px solid #000; text-align:center; font-weight:bold; font-size:12px;'>
                        <div style='width:50%; float:left; {left_style_total} padding:5px 0;'>{pos_total}</div>
                        <div style='width:50%; float:right; {right_style_total} padding:5px 0;'>{neg_total}</div>
                        <div style='clear:both;'></div>
                    </div>
                """

            self.env['weekly.feedback.report'].sudo().create(vals)

        return {
            'name': f"Weekly Feedback Report ({self.start_date.strftime('%d-%b-%Y')} - {self.end_date.strftime('%d-%b-%Y')})",
            'type': 'ir.actions.act_window',
            'res_model': 'weekly.feedback.report',
            'view_mode': 'tree',
            'target': 'current',
        }