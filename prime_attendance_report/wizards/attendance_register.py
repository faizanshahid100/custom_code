import base64
import datetime
import io
from datetime import datetime, timedelta, date
import xlsxwriter
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class EmployeeAttendanceRegister(models.TransientModel):
    _name = 'employee.attendance.register'
    _description = 'Employee Attendance Register'

    @api.model
    def default_get(self, default_fields):
        res = super(EmployeeAttendanceRegister, self).default_get(default_fields)

        # Get user's linked employee
        user = self.env.user
        employee = self.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)

        # Default timezone offset
        utc_offset = 0

        # Determine offset based on employee's country
        if employee and employee.country_id:
            country = employee.country_id.name
            if country == 'Pakistan':
                utc_offset = 5
            elif country == 'Philippines':
                utc_offset = 8

        today = date.today()

        # First day of current month at 00:00
        first_day_current_month = datetime(
            year=today.year,
            month=today.month,
            day=1,
            hour=0,
            minute=0
        ) - timedelta(hours=utc_offset)

        end_date = datetime(
            year=today.year,
            month=today.month,
            day=today.day,
            hour=23,
            minute=59
        ) - timedelta(hours=utc_offset)

        res.update({
            'start_date': first_day_current_month,
            'end_date': end_date,
        })
        return res

    employee_ids = fields.Many2many('hr.employee', 'employee_rel', 'category_id', string='Employee Wise', required=True)
    start_date = fields.Datetime('Start Date', required=True)
    end_date = fields.Datetime('End Date', required=True)
    absent = fields.Char('Absent', default='A')

    def get_data(self):
        date_list = []
        start_date = self.start_date
        end_date = self.end_date
        delta = relativedelta(days=1)
        while start_date <= end_date:
            date_list.append({
                "date_list": start_date.day,
            })
            start_date += delta
        return date_list

    def check_attendance(self):
        data = []
        report = self.env['hr.attendance'].search(
            [('employee_id', 'in', self.employee_ids.ids), ('check_in', '>=', self.start_date),
             ('check_in', '<=', self.end_date + timedelta(days=1))])  # Slight buffer for timezone shift

        for rec in report:
            check_in = rec.check_in + timedelta(hours=5) if rec.check_in else None
            check_out = rec.check_out + timedelta(hours=5) if rec.check_out else None

            if check_in and check_out:
                work_hours = round(rec.worked_hours, 1)
                data.append({
                    'date': check_in.date().day,
                    'state': work_hours,
                    'employee': rec.employee_id.id,
                    'department': rec.employee_id.department_id.id,
                })

        # Remove duplicates if any
        res_list = [i for n, i in enumerate(data) if i not in data[n + 1:]]
        return res_list

    def calculate_employee_off_days(self, emp, start_date, end_date):
        if not emp.resource_calendar_id:
            raise ValueError("Employee has no working schedule assigned.")
        off_days = []
        working_hours = emp.resource_calendar_id
        working_days = set(attendance.dayofweek for attendance in working_hours.attendance_ids)
        date_range = [
            (start_date + timedelta(days=i))
            for i in range((end_date - start_date).days + 1)
        ]
        for date in date_range:
            if str(date.weekday()) not in working_days:
                off_days.append(date.day)
        return off_days

    def get_employee_leave_dates(self, emp, start_date, end_date):
        leave_records = self.env['hr.leave'].search([
            ('employee_id', '=', emp.id),
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

    def get_before_contract(self, emp, start_date, end_date):
        flag = False
        day_numbers = []
        if emp.joining_date:
            if start_date <= emp.joining_date <= end_date:
                flag = True
                day_numbers = list(range(1, emp.joining_date.day + 1))
            else:
                flag = False
        return flag, day_numbers

    def export_to_excel(self):
        data = self.check_attendance()
        date_range = self.get_data()
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Attendance Report')
        header_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'size': 16,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': '#8EA9DB',
        })
        table_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'size': 11,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': '#8EA9DB',
        })
        date_format = workbook.add_format({
            'num_format': 'dd/mm/yy',
            'align': 'left',
            "valign": 'vcenter',
            'font_size': '11',
        })
        format_absent = workbook.add_format({
            'bg_color': '#FF5B61',
            'font_color': 'white',
            'align': 'center',
            'border': 1,
        })
        format_leave = workbook.add_format({
            'bg_color': '#fff766',
            'font_color': 'white',
            'color': 'black',
            'align': 'center',
            'border': 1,
        })
        format_off_day = workbook.add_format({
            'bg_color': '#9c9191',
            'font_color': 'white',
            'align': 'center',
            'border': 1,
        })
        format_present = workbook.add_format({
            'bg_color': '#D1FFBD',
            'align': 'center',
            'border': 1,
        })
        worksheet.set_column('A:A', 5)
        worksheet.set_column('B:D', 30)
        worksheet.set_column('E:E', 10)
        worksheet.set_column('F:DK', 12)

        # Title
        worksheet.merge_range('B2:Y3', 'Attendance Report', header_format)
        worksheet.write('B5', "Date From :")
        worksheet.write('C5', self.start_date, date_format)
        worksheet.write('B6', "Date To :")
        worksheet.write('C6', self.end_date, date_format)
        days_list = []
        for date_dict in date_range:
            day = date_dict['date_list']
            month = self.start_date.month
            year = self.start_date.year
            full_date = datetime(year, month, day)
            day_of_week = full_date.strftime("%d %b")
            days_list.append(day_of_week)

        # Write headers
        headers_days = ['', '', '', '', ''] + [d for d in days_list] + ['', '']
        for col, header in enumerate(headers_days):
            worksheet.write(7, col, header, table_format)

        headers = ['S.No', 'Name of Employee', 'Department', 'Designation', 'Gender'] + [f'{d["date_list"]}' for d in
                                                                                         date_range] + [
                      'Total Hours', 'No of days']
        for col, header in enumerate(headers):
            worksheet.write(8, col, header, table_format)

        # Write employee data
        row = 9
        for index, employee in enumerate(self.employee_ids):
            present_days = 0
            worksheet.write(row, 0, index + 1)
            worksheet.write(row, 1, employee.name)
            worksheet.write(row, 2, employee.department_id.name if employee.department_id else '')
            worksheet.write(row, 3, employee.job_id.name if employee.job_id else '')
            worksheet.write(row, 4, dict(employee._fields['gender'].selection).get(employee.gender) or '')

            total_hours = 0.0  # Variable to keep track of total hours worked for each employee

            attn_dates = {att['date']: att['state'] for att in data if att['employee'] == employee.id}
            off_day = self.calculate_employee_off_days(employee, self.start_date, self.end_date)
            leaves_day = self.get_employee_leave_dates(employee, self.start_date, self.end_date)
            before_contract_flag = self.get_before_contract(employee, self.start_date, self.end_date)[0]
            before_contract_date = self.get_before_contract(employee, self.start_date, self.end_date)[1]
            for col, date in enumerate(date_range, start=5):
                date_val = date['date_list']
                state = attn_dates.get(date_val, self.absent)
                # cell_format = format_present if state != self.absent else format_absent
                if state != self.absent:
                    total_hours += state  # Sum the working hours for the employee
                    worksheet.write(row, col, state if state != self.absent else self.absent, format_present)
                    present_days += 1
                if state == "A":
                    if before_contract_flag:
                        if date['date_list'] in before_contract_date:
                            worksheet.write(row, col, "-", format_off_day)
                        else:
                            worksheet.write(row, col, state if state != self.absent else self.absent, format_absent)
                    elif date['date_list'] in leaves_day:
                        worksheet.write(row, col, "Leave", format_leave)
                    elif date['date_list'] in off_day:
                        worksheet.write(row, col, "Rest", format_off_day)
                    else:
                        worksheet.write(row, col, state if state != self.absent else self.absent, format_absent)

            # Write total hours in the last column
            worksheet.write(row, len(headers) - 2, round(total_hours, 2) or "", table_format)
            # worksheet.write(row, len(headers) - 1, round(total_hours / employee.total_working_hour, 1) or "", table_format)
            worksheet.write(row, len(headers) - 1, present_days or "", table_format)

            row += 1

        workbook.close()
        output.seek(0)
        file_data = output.read()
        output.close()

        attachment = self.env['ir.attachment'].create({
            'name': 'attendance_report.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(file_data),
            'store_fname': 'attendance_report.xlsx',
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }
