from odoo import api, fields, models, registry, _
from dateutil.relativedelta import relativedelta
import datetime
import io
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
    department_id = fields.Many2one('hr.department', string='Department', domain=[('name', 'in', ('Tech PH', 'Tech PK', 'Business PH', 'Business PK'))])
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

    # def action_confirm_tickets(self):
    #     if self.department_id:
    #         employees = self.env['hr.employee'].search([('department_id', '=', self.department_id.id)])
    #     elif not self.department_id:
    #         employees = self.env['hr.employee'].search([])
    #
    #     # Step 1: Define headers
    #     headers = [
    #         'Employee Name', 'Job Position', 'Department',
    #         'Contractor', 'Manager (Contractor)', 'Manager',
    #         'Gender', 'Level'
    #     ]
    #
    #     # Step 2: Prepare weekly date ranges
    #     def get_week_ranges(start_date, end_date):
    #         ranges = []
    #         current = start_date
    #         while current <= end_date:
    #             week_end = current + timedelta(days=6 - current.weekday())
    #             if week_end > end_date:
    #                 week_end = end_date
    #             ranges.append((current, week_end))
    #             current = week_end + timedelta(days=1)
    #         return ranges
    #
    #     week_ranges = get_week_ranges(self.start_date, self.end_date)
    #
    #     # Append week headers
    #     week_headers = [f"Week {i + 1}\n({start.strftime('%d-%b')} - {end.strftime('%d-%b')})" for i, (start, end)
    #                     in enumerate(week_ranges)]
    #     headers.extend(week_headers)
    #
    #     # Step 3: Fetch daily.progress records
    #     progresses = self.env['daily.progress'].search([
    #         ('date_of_project', '>=', self.start_date),
    #         ('date_of_project', '<=', self.end_date),
    #         ('resource_user_id.employee_id', 'in', employees.ids)
    #     ])
    #
    #     # Group data: employee_id -> week_index -> ticket total
    #     progress_map = defaultdict(lambda: defaultdict(int))
    #     for progress in progresses:
    #         emp_id = progress.resource_user_id.employee_id.id
    #         project_date = progress.date_of_project
    #         for index, (start, end) in enumerate(week_ranges):
    #             if start <= project_date <= end:
    #                 progress_map[emp_id][index] += progress.avg_resolved_ticket
    #                 break
    #
    #     # Step 4: Generate Excel
    #     output = io.BytesIO()
    #     workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    #     worksheet = workbook.add_worksheet("Weekly Tickets")
    #     worksheet.set_column('A:B', 25)
    #     worksheet.set_column('C:C', 16)
    #     worksheet.set_column('D:F', 25)
    #     worksheet.set_column('G:AH', 16)
    #
    #     bold = workbook.add_format({'bold': True, 'bg_color': '#8EA9DB', 'border': 1})
    #     normal = workbook.add_format({'border': 1})
    #
    #     # Write headers
    #     for col, header in enumerate(headers):
    #         worksheet.write(0, col, header, bold)
    #
    #     # Write employee data
    #     row = 1
    #     for employee in employees:
    #         values = [
    #             employee.name or '',
    #             employee.job_id.name or '',
    #             employee.department_id.name or '',
    #             employee.contractor.name or '',
    #             employee.manager or '',
    #             employee.parent_id.name or '',
    #             dict(employee._fields['gender'].selection).get(employee.gender) or '',
    #             employee.level or '',
    #         ]
    #         for col, val in enumerate(values):
    #             worksheet.write(row, col, val, normal)
    #
    #         # Weekly tickets
    #         for week_index in range(len(week_ranges)):
    #             tickets = progress_map[employee.id].get(week_index, 0)
    #             worksheet.write(row, len(values) + week_index, tickets, normal)
    #
    #         row += 1
    #
    #     workbook.close()
    #     output.seek(0)
    #     file_data = output.read()
    #     output.close()
    #
    #     attachment = self.env['ir.attachment'].create({
    #         'name': 'weekly_tickets.xlsx',
    #         'type': 'binary',
    #         'datas': base64.b64encode(file_data),
    #         'store_fname': 'weekly_ticket.xlsx',
    #         'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    #     })
    #
    #     return {
    #         'type': 'ir.actions.act_url',
    #         'url': '/web/content/%s?download=true' % attachment.id,
    #         'target': 'self',
    #     }

    # def action_confirm_feedbacks(self):
    #     from collections import defaultdict
    #     import io
    #     import base64
    #     import xlsxwriter
    #
    #     # Get employees
    #     domain = []
    #     if self.department_id:
    #         domain.append(('department_id', '=', self.department_id.id))
    #     employees = self.env['hr.employee'].search(domain)
    #
    #     # Prepare week ranges
    #     def get_week_ranges(start_date, end_date):
    #         ranges = []
    #         current = start_date
    #         while current <= end_date:
    #             week_end = current + timedelta(days=6 - current.weekday())
    #             if week_end > end_date:
    #                 week_end = end_date
    #             ranges.append((current, week_end))
    #             current = week_end + timedelta(days=1)
    #         return ranges
    #
    #     week_ranges = get_week_ranges(self.start_date, self.end_date)
    #
    #     # Get feedback records
    #     feedbacks = self.env['hr.employee.feedback'].search([
    #         ('employee_id', 'in', employees.ids),
    #         ('date_feedback', '>=', self.start_date),
    #         ('date_feedback', '<=', self.end_date)
    #     ])
    #
    #     # Prepare feedback map: emp_id → week_index → {'positive': X, 'negative': Y}
    #     feedback_map = defaultdict(lambda: defaultdict(lambda: {'positive': 0, 'negative': 0}))
    #     for fb in feedbacks:
    #         emp_id = fb.employee_id.id
    #         for idx, (start, end) in enumerate(week_ranges):
    #             if start <= fb.date_feedback <= end:
    #                 feedback_map[emp_id][idx][fb.feedback_type] += 1
    #                 break
    #
    #     # Build Excel
    #     output = io.BytesIO()
    #     workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    #     worksheet = workbook.add_worksheet("Weekly Feedbacks")
    #
    #     # Set column widths
    #     worksheet.set_column('A:B', 25)
    #     worksheet.set_column('C:C', 16)
    #     worksheet.set_column('D:F', 25)
    #     worksheet.set_column('G:H', 16)
    #     worksheet.set_column('I:ZZ', 30)
    #
    #     # Formats
    #     bold = workbook.add_format({'bold': True, 'bg_color': '#8EA9DB', 'border': 1})
    #     normal = workbook.add_format({'border': 1})
    #
    #     # Headers
    #     base_headers = [
    #         'Employee Name', 'Job Position', 'Department',
    #         'Contractor', 'Manager (Contractor)', 'Manager',
    #         'Gender', 'Level',
    #     ]
    #
    #     week_headers = []
    #     for i, (start, end) in enumerate(week_ranges):
    #         label = f"Week {i + 1} ({start.strftime('%d-%b')} - {end.strftime('%d-%b')})"
    #         week_headers.append(f"{label} (Pos)")
    #         week_headers.append(f"{label} (Neg)")
    #
    #     headers = base_headers + week_headers
    #
    #     # Write headers
    #     for col, header in enumerate(headers):
    #         worksheet.write(0, col, header, bold)
    #
    #     # Write employee data
    #     row = 1
    #     for emp in employees:
    #         base_data = [
    #             emp.name or '',
    #             emp.job_id.name or '',
    #             emp.department_id.name or '',
    #             emp.contractor.name or '',
    #             emp.manager or '',
    #             emp.parent_id.name or '',
    #             dict(emp._fields['gender'].selection).get(emp.gender) or '',
    #             emp.level or '',
    #         ]
    #         for col, val in enumerate(base_data):
    #             worksheet.write(row, col, val, normal)
    #
    #         # Weekly feedbacks
    #         for i in range(len(week_ranges)):
    #             pos = feedback_map[emp.id][i].get('positive', 0)
    #             neg = feedback_map[emp.id][i].get('negative', 0)
    #             worksheet.write(row, len(base_data) + i * 2, pos, normal)
    #             worksheet.write(row, len(base_data) + i * 2 + 1, neg, normal)
    #
    #         row += 1
    #
    #     workbook.close()
    #     output.seek(0)
    #     file_data = output.read()
    #     output.close()
    #
    #     # Create attachment
    #     attachment = self.env['ir.attachment'].create({
    #         'name': 'weekly_feedbacks.xlsx',
    #         'type': 'binary',
    #         'datas': base64.b64encode(file_data),
    #         'store_fname': 'weekly_feedbacks.xlsx',
    #         'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    #     })
    #
    #     return {
    #         'type': 'ir.actions.act_url',
    #         'url': '/web/content/%s?download=true' % attachment.id,
    #         'target': 'self',
    #     }

    def action_confirm_tickets(self):
        if self.department_id:
            employees = self.env['hr.employee'].sudo().search([('department_id', '=', self.department_id.id)])
        else:
            employees = self.env['hr.employee'].sudo().search([('department_id.name', 'in', ('Tech PH', 'Tech PK', 'Business PH', 'Business PK'))])

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

        # Start from very first coming Monday
        self.start_date = self.start_date + timedelta(days=(7 - self.start_date.weekday()) % 7)
        week_ranges = get_week_ranges(self.start_date, self.end_date)

        progresses = self.env['daily.progress'].sudo().search([
            ('date_of_project', '>=', self.start_date),
            ('date_of_project', '<=', self.end_date),
            ('resource_user_id.employee_id', 'in', employees.ids)
        ])

        progress_map = defaultdict(lambda: defaultdict(int))
        for progress in progresses:
            emp_id = progress.resource_user_id.employee_id.id
            for index, (start, end) in enumerate(week_ranges):
                if start <= progress.date_of_project <= end:
                    progress_map[emp_id][index + 1] += progress.avg_resolved_ticket
                    break

        self.env['weekly.ticket.report'].sudo().search([]).unlink()

        # Create records in weekly.ticket.report
        for employee in employees:
            weekly_tickets = employee.d_ticket_resolved * 5
            vals = {
                'employee_id': employee.id,
            }


            resolved_tickets_total = 0
            all_tickets_total = 0
            for week_index in range(1, len(week_ranges)+1):
                if employee.kpi_measurement == 'kpi':
                    resolved_tickets_total += progress_map[employee.id].get(week_index, 0)
                    all_tickets_total += weekly_tickets
                    if progress_map[employee.id].get(week_index, 0) >= weekly_tickets:
                        vals[
                            f'week_{week_index}'] = f"<div style='background-color: #c6efce; padding: 3px;text-align: center;'>{progress_map[employee.id].get(week_index, 0)} / {weekly_tickets}</div>"
                    else:
                        vals[
                            f'week_{week_index}'] = f"<div style='background-color: #ff0000; color: white; padding: 3px;text-align: center;'>{progress_map[employee.id].get(week_index, 0)} / {weekly_tickets}</div>"
                else:
                    vals[
                        f'week_{week_index}'] = f"<div style='padding: 3px;text-align: center;'>{progress_map[employee.id].get(week_index, 0)}</div>"
                if employee.kpi_measurement == 'kpi':
                    vals['week_total'] = f"<div style='background-color: #c6efce; padding: 3px;text-align: center;border: 2px solid #000;'><b>{resolved_tickets_total} / {all_tickets_total}</b></div>" if resolved_tickets_total >= all_tickets_total else f"<div style='background-color: #ff0000; color: white; padding: 3px;text-align: center;border: 2px solid #000;'><b>{resolved_tickets_total} / {all_tickets_total}</b></div>"

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
            employees = self.env['hr.employee'].sudo().search([('department_id.name', 'in', ('Tech PH', 'Tech PK', 'Business PH', 'Business PK'))])

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
