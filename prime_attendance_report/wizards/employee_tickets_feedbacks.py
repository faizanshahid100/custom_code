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
    department_id = fields.Many2one('hr.department', string='Department')

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
            employees = self.env['hr.employee'].search([('department_id', '=', self.department_id.id)])
        else:
            employees = self.env['hr.employee'].search([])

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

        progresses = self.env['daily.progress'].search([
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

        self.env['weekly.ticket.report'].search([]).unlink()

        # Create records in weekly.ticket.report
        for employee in employees:
            weekly_tickets = employee.d_ticket_resolved*5
            vals = {
                'employee_id': employee.id,
            }

            # Add week_1 to week_26
            for week_index in range(1, 27):
                if employee.kpi_measurement == 'kpi':
                    if progress_map[employee.id].get(week_index, 0) >= weekly_tickets:
                        vals[f'week_{week_index}'] = f"<div style='background-color: #c6efce; padding: 3px;text-align: center;'>{progress_map[employee.id].get(week_index, 0)}</div>"
                    else:
                        vals[
                            f'week_{week_index}'] = f"<div style='background-color: #ff0000; color: white; padding: 3px;text-align: center;'>{progress_map[employee.id].get(week_index, 0)}</div>"
                else:
                    vals[
                        f'week_{week_index}'] = f"<div style='padding: 3px;text-align: center;'>{progress_map[employee.id].get(week_index, 0)}</div>"

            self.env['weekly.ticket.report'].create(vals)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Weekly Ticket Report',
            'res_model': 'weekly.ticket.report',
            'view_mode': 'tree',
            'target': 'current',
        }


    def action_confirm_feedbacks(self):
        if self.department_id:
            employees = self.env['hr.employee'].search([('department_id', '=', self.department_id.id)])
        else:
            employees = self.env['hr.employee'].search([])

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

        feedbacks = self.env['hr.employee.feedback'].search([
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

        self.env['weekly.feedback.report'].search([]).unlink()

        for emp in employees:
            vals = {
                'employee_id': emp.id,
            }

            for i in range(1, 27):  # up to 26 weeks
                pos = feedback_map[emp.id][i]['positive']
                neg = feedback_map[emp.id][i]['negative']
                if pos:
                    vals[f'week_{i}'] = f"<div style='background-color:#c6efce;text-align:center; border:1px solid #000;'>+ve</div>"
                elif neg:
                    vals[f'week_{i}'] = f"<div style='background-color:#ffc7ce;text-align:center; border:1px solid #000;'>-ve</div>"
                else:
                    vals[f'week_{i}'] = f"<div style='text-align:center; border:1px solid #000;padding:10px;'></div>"

            self.env['weekly.feedback.report'].create(vals)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Weekly Feedback Report',
            'res_model': 'weekly.feedback.report',
            'view_mode': 'tree',
            'target': 'current',
        }