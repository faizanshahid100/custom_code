# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError, UserError
import io
import base64
from datetime import timedelta
import xlsxwriter


class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'


    def _get_available_contracts_domain(self):
        return [('contract_ids.state', 'in', ('open', 'close')), ('company_id', '=', self.env.company.id)]

    def _get_employees(self):
        active_employee_ids = self.env.context.get('active_employee_ids', False)
        if active_employee_ids:
            employees_slip = self.env['hr.employee'].browse(active_employee_ids)
            return employees_slip
            # employees_end = employees_slip.search([('stop_salary','=',False)])
            # return employees_end
        # YTI check dates too
        final_emp_list = self.env['hr.employee'].search(self._get_available_contracts_domain())
        return final_emp_list
        # final_emp = final_emp_list.search([('stop_salary','=',False)])
        # return final_emp


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    currency_id = fields.Many2one(related='contract_id.payslip_currency_id')

    def compute_sheet(self):
        for payslip in self:
            date_from = str(payslip.date_from)
            year = int(date_from[:4])  # Extract year
            month = int(date_from[-5:-3])  # Extract month

            # Determine the number of days in the month, including leap year handling for February
            if month in {1, 3, 5, 7, 8, 10, 12}:
                days = 31
            elif month == 2:
                days = 29 if (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)) else 28
            else:
                days = 30

            employee_wage = payslip.employee_id.contract_id.wage
            per_day_employee_wage = employee_wage / days

            data=[]
            ############################ ATTENDANCE COUNT ##############################
            """Attendance Count"""
            attendances = self.env['hr.attendance'].search([('employee_id','=',payslip.employee_id.id),('att_date','>=',payslip.date_from),('att_date','<=',payslip.date_to)])
            attendance_day = 0
            attendance_hours = 0
            for att in attendances:
                attendance_day += 1
                attendance_hours += att.worked_hours
            att_end = self.env['hr.work.entry.type'].search([('code','=','WORK100')], limit=1)
            data.append((0,0,{
                'payslip_id': payslip.id,
                'work_entry_type_id': att_end.id,
                'name': att_end.name,
                'number_of_days': attendance_day,
                'number_of_hours': attendance_hours,
                'amount': attendance_day * per_day_employee_wage,
            }))
            ############################ LEAVE COUNT ##############################
            """Leave Count"""
            leaves = self.env['hr.leave'].search([('employee_id','=',payslip.employee_id.id),('date_from','>=',payslip.date_from),('date_to','<=',payslip.date_to),('state','=','validate')])
            leaves_entry_type = leaves.holiday_status_id.work_entry_type_id
            total_leaves = 0

            for entry in leaves_entry_type:
                leave_days = 0
                for lv in leaves:
                    if lv.holiday_status_id.work_entry_type_id.code == entry.code:
                        leave_days += lv.number_of_days_display
                total_leaves += leave_days
                data.append((0,0,{
                    'payslip_id': payslip.id,
                    'work_entry_type_id': entry.id,
                    'name': entry.name,
                    'number_of_days':leave_days,
                }))
            ############################ REST DAYS COUNT ##############################
            """Rest Day Count/Generic Time Off"""
            # Get employee's working schedule
            working_schedule = payslip.employee_id.resource_calendar_id

            # Fetch working days from schedule (Monday=0, Sunday=6)
            working_days = working_schedule.attendance_ids.mapped('dayofweek')  # List of working days as string

            # Convert to integers for easy comparison
            working_days = list(map(int, working_days))

            # Get total days in payslip range
            total_days = (payslip.date_to - payslip.date_from).days + 1

            # Initialize variables
            off_days_count = 0
            current_date = payslip.date_from

            # Loop through each date in the range
            for _ in range(total_days):
                if current_date.weekday() not in working_days:  # If not a working day, count as off day
                    off_days_count += 1
                current_date += timedelta(days=1)  # Move to next day

            # Store the calculated off days in the payslip work entry type
            off_day_entry = self.env['hr.work.entry.type'].search([('code', '=', 'LEAVE100')], limit=1)
            data.append((0, 0, {
                'payslip_id': payslip.id,
                'work_entry_type_id': off_day_entry.id,
                'name': off_day_entry.name,
                'number_of_days': off_days_count,
            }))
            ############################ REST DAY COUNT OLD(Soon removed) ##############################
            # day = (payslip.date_to - payslip.date_from).days + 1
            # start_date = payslip.date_from
            # rest_day_count = 0
            # for ia in range(day):
            #     start_date = start_date + timedelta(1)
            #     # Working Schedule
            #     attendance_present = self.env['resource.calendar.attendance'].sudo().search([('dayofweek','=',start_date.weekday()),('calendar_id','=',payslip.employee_id.resource_calendar_id.id)], limit=1)
            #     attendd = self.env['hr.attendance'].search([('employee_id' ,'=', payslip.employee_id.id),('att_date' ,'=', start_date)], limit=1)
            #     remain_day = 0
            #     if attendd:
            #         remain_day = 1 - attendance_day
            #     if not attendance_present:
            #         rest_day_count+= 1 - remain_day
            #
            # rest_day_end = self.env['hr.work.entry.type'].search([('code','=','LEAVE100')], limit=1)
            # data.append((0,0,{
            #     'payslip_id': payslip.id,
            #     'work_entry_type_id': rest_day_end.id,
            #     'name': rest_day_end.name,
            #     'number_of_days':rest_day_count,
            # }))
            ############################ ABSENT DAYS COUNT ##############################
            """Absent Count"""
            total_counts = attendance_day  + total_leaves + off_days_count
            absent_day = (total_days - total_counts)
            absent_day_end = self.env['hr.work.entry.type'].search([('code', '=', 'OUT')], limit=1)
            data.append((0, 0, {
                'payslip_id': payslip.id,
                'work_entry_type_id': absent_day_end.id,
                'name': absent_day_end.name,
                'number_of_days': absent_day,
            }))

            """Overtime Count"""
            overtime = self.env['approval.request'].search(
                [('category_id.sequence_code', '=', 'OVERTIME')
                 , ('request_owner_id', '=', payslip.employee_id.user_id.id),
                 ('date_start', '>=', payslip.date_from), ('date_end', '<=', payslip.date_to),
                 ('request_status', '=', 'approved')])
            overtime_hours = 0
            for att in overtime:
                hours = (att.date_end - att.date_start).total_seconds() / 3600  # Convert to hours
                # Accumulate overtime hours
                overtime_hours += hours
            att_end = self.env['hr.work.entry.type'].search([('code', '=', 'OVERTIME')], limit=1)
            # data.append((0, 0, {
            #     'payslip_id': payslip.id,
            #     'work_entry_type_id': att_end.id,
            #     'name': att_end.name,
            #     'number_of_hours': overtime_hours,
            #     'amount': 0,
            # }))
            payslip.worked_days_line_ids.unlink()
            payslip.worked_days_line_ids=data

        res = super(HrPayslip, self).compute_sheet()
        return res

    def action_payment_slips_details_report(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Payslip Report')
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
        worksheet.set_column('A:C', 10)
        worksheet.set_column('D:D', 22)
        worksheet.set_column('E:E', 25)
        worksheet.set_column('F:F', 33)
        worksheet.set_column('G:G', 22)
        worksheet.set_column('H:J', 15)
        worksheet.set_column('K:AC', 22)

        # Title
        worksheet.merge_range('B2:L3', 'Payroll Report', header_format)
        # worksheet.write('B5', "Date From :")
        # worksheet.write('C5', self.date_from, date_format)
        # worksheet.write('B6', "Date To :")
        # worksheet.write('C6', self.date_to, date_format)

        headers = ['Sr. No.', 'Slip No.', 'Emp Code', 'Identification Number', 'Employee Name', 'Designation', 'Department', 'Country','Month Days', 'Payment Days' , 'Basic Salary (PKR)', 'Total Salary (PKR)', 'Bonus / Arrear(PKR)', 'Increment Arrear  (PKR)', 'Iftar Allowance (PKR)', 'Overtime  (PKR)', 'Reimbursments (PKR)', 'Loan & Advances  (PKR)', 'Others Deduction  (PKR)', '.25% WHT for UAE', '$10 Bank Charges', 'Net Payment  (PKR)', 'Net Payment  (USD)', 'Status', 'Joining Dates', 'Account Number', 'Account  Details', 'Bank Name', 'Home Address']
        for col, header in enumerate(headers):
            worksheet.write(4, col, header, table_format)

        # Write payslip data
        row = 5
        for sr_no, payslip in enumerate(self):
            worksheet.write(row, 0, sr_no + 1)
            worksheet.write(row, 1, payslip.number)
            worksheet.write(row, 2, payslip.employee_id.barcode)
            worksheet.write(row, 3, payslip.employee_id.identification_id)
            worksheet.write(row, 4, payslip.employee_id.name)
            worksheet.write(row, 5, payslip.employee_id.job_id.name if payslip.employee_id.job_id else '')
            worksheet.write(row, 6, payslip.employee_id.department_id.name if payslip.employee_id.department_id else '')
            worksheet.write(row, 7, payslip.employee_id.country_id.name or '')
            worksheet.write(row, 8, payslip.date_to.day or '')
            worksheet.write(row, 9, '')
            worksheet.write(row, 10, f"{', '.join(f'{line.total:,.2f}' for line in payslip.line_ids.filtered(lambda l: l.name == 'Basic Salary') if line.total)}")
            worksheet.write(row, 11, f'{sum(payslip.line_ids.filtered(lambda l: l.category_id.name == "Allowance").mapped("total")):,.2f}')
            worksheet.write(row, 12, '')
            worksheet.write(row, 13, '')
            worksheet.write(row, 14, '')
            worksheet.write(row, 15, f"{', '.join(f'{line.total:,.2f}' for line in payslip.line_ids.filtered(lambda l: l.name == 'Overtime Pay') if line.total)}")
            worksheet.write(row, 16, '')
            worksheet.write(row, 17, '')
            worksheet.write(row, 18, f'{sum(payslip.line_ids.filtered(lambda l: l.category_id.name == "Deduction").mapped("total")):,.2f}')
            worksheet.write(row, 19, '')
            worksheet.write(row, 20, '')
            worksheet.write(row, 21, f"{', '.join(f'{line.total:,.2f}' for line in payslip.line_ids.filtered(lambda l: l.name == 'Net Salary') if line.total)}")
            worksheet.write(row, 24, payslip.employee_id.joining_date.strftime('%d %b %Y') or '')
            worksheet.write(row, 25, payslip.employee_id.bank_account_id.acc_number or '')
            worksheet.write(row, 26, '\n'.join(
                part for part in [
                    f"Title: {payslip.employee_id.bank_account_id.acc_holder_name}" if payslip.employee_id.bank_account_id.acc_holder_name else '',
                    f"IBAN: {payslip.employee_id.bank_account_id.iban}" if payslip.employee_id.bank_account_id.iban else '',
                    f"SWIFT: {payslip.employee_id.bank_account_id.swift}" if payslip.employee_id.bank_account_id.swift else '',
                    f"Code: {payslip.employee_id.bank_account_id.code}" if payslip.employee_id.bank_account_id.code else ''
                ] if part
            ))
            worksheet.write(row, 27, payslip.employee_id.bank_account_id.bank_id.name or '')
            worksheet.write(row, 28, payslip.employee_id.address_home_id.name)


            row += 1

        workbook.close()
        output.seek(0)
        file_data = output.read()
        output.close()

        attachment = self.env['ir.attachment'].create({
            'name': 'payslip_report.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(file_data),
            'store_fname': 'payslip_report.xlsx',
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }

    def print_payslip_pdf(self):
        return self.env.ref('ws_hr_payroll_entries.action_report_payslip_custom').report_action(self)