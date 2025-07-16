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
    wht_uae_amount = fields.Float(store=True)

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

            data = []
            ############################ ATTENDANCE COUNT ##############################
            """Attendance Count"""
            attendances = self.env['hr.attendance'].search(
                [('employee_id', '=', payslip.employee_id.id), ('att_date', '>=', payslip.date_from),
                 ('att_date', '<=', payslip.date_to)])
            attendance_day = 0
            attendance_hours = 0
            for att in attendances:
                attendance_day += 1
                attendance_hours += att.worked_hours
            att_end = self.env['hr.work.entry.type'].search([('code', '=', 'WORK100')], limit=1)
            data.append((0, 0, {
                'payslip_id': payslip.id,
                'work_entry_type_id': att_end.id,
                'name': att_end.name,
                'number_of_days': attendance_day,
                'number_of_hours': attendance_hours,
                'amount': attendance_day * per_day_employee_wage,
            }))
            ############################ LEAVE COUNT ##############################
            """Leave Count"""
            leaves = self.env['hr.leave'].search(
                [('employee_id', '=', payslip.employee_id.id), ('date_from', '>=', payslip.date_from),
                 ('date_to', '<=', payslip.date_to), ('state', '=', 'validate')])
            leaves_entry_type = leaves.holiday_status_id.work_entry_type_id
            total_leaves = 0

            for entry in leaves_entry_type:
                leave_days = 0
                for lv in leaves:
                    if lv.holiday_status_id.work_entry_type_id.code == entry.code:
                        leave_days += lv.number_of_days_display
                total_leaves += leave_days
                data.append((0, 0, {
                    'payslip_id': payslip.id,
                    'work_entry_type_id': entry.id,
                    'name': entry.name,
                    'number_of_days': leave_days,
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
            total_counts = attendance_day + total_leaves + off_days_count
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
            payslip.worked_days_line_ids = data
            payslip._compute_wht_uae()

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
        worksheet.set_column('H:M', 15)
        worksheet.set_column('N:AJ', 22)

        # Title
        worksheet.merge_range('B2:L3', 'Payroll Report', header_format)
        # worksheet.write('B5', "Date From :")
        # worksheet.write('C5', self.date_from, date_format)
        # worksheet.write('B6', "Date To :")
        # worksheet.write('C6', self.date_to, date_format)

        headers = ['Sr. No.', 'Slip No.', 'Emp Code', 'Identification Number', 'Employee Name', 'Designation',
                   'Department', 'Country', 'Month Days', 'Payment Days', 'Basic Salary', 'Travel Allowances',
                   'Fuel Allowances', 'Relocation Allowances', 'Total Salary', 'Referral Bonus', 'Performance Bonus',
                   'Wedding Bonus', 'Increment Arrear', 'Iftar Allowance', 'Overtime', 'Reimbursement Medical', 'Fuel',
                   'Mobile', 'Certifications', 'Conversion Rate', 'Travel', 'Subscription', 'Loan & Advances',
                   'Others Deduction', '0.25% WHT for UAE', '$10 Bank Charges', 'Net Payment', 'Net Payment (USD)',
                   'Status', 'Joining Dates', 'Account Number', 'Account Details', 'Bank Name', 'Home Address']
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
            worksheet.write(row, 10,
                            f"{', '.join(f'{line.total:,.2f}' for line in payslip.line_ids.filtered(lambda l: l.salary_rule_id.name == 'Basic Salary') if line.total)}")
            worksheet.write(row, 11,
                            f"{', '.join(f'{line.total:,.2f}' for line in payslip.line_ids.filtered(lambda l: l.salary_rule_id.name == 'Travel Allowance') if line.total)}")
            worksheet.write(row, 12,
                            f"{', '.join(f'{line.total:,.2f}' for line in payslip.line_ids.filtered(lambda l: l.salary_rule_id.name == 'Fuel Allowance') if line.total)}")
            worksheet.write(row, 13,
                            f"{', '.join(f'{line.total:,.2f}' for line in payslip.line_ids.filtered(lambda l: l.salary_rule_id.name == 'Relocation Allowance') if line.total)}")
            worksheet.write(row, 14,
                            f'{sum(payslip.line_ids.filtered(lambda l: l.category_id.name in ["Allowance", "Basic"]).mapped("total")):,.2f}')
            worksheet.write(row, 15,
                            f"{', '.join(f'{line.total:,.2f}' for line in payslip.line_ids.filtered(lambda l: l.salary_rule_id.name == 'Bonus Referral') if line.total)}")
            worksheet.write(row, 16,
                            f"{', '.join(f'{line.total:,.2f}' for line in payslip.line_ids.filtered(lambda l: l.salary_rule_id.name == 'Bonus Performance') if line.total)}")
            worksheet.write(row, 17,
                            f"{', '.join(f'{line.total:,.2f}' for line in payslip.line_ids.filtered(lambda l: l.salary_rule_id.name == 'Bonus Wedding') if line.total)}")
            worksheet.write(row, 18, '0')  # TODO
            worksheet.write(row, 19, '0')  # TODO
            worksheet.write(row, 20,
                            f"{', '.join(f'{line.total:,.2f}' for line in payslip.line_ids.filtered(lambda l: l.salary_rule_id.name == 'Overtime') if line.total)}")
            worksheet.write(row, 21,
                            f"{', '.join(f'{line.total:,.2f}' for line in payslip.line_ids.filtered(lambda l: l.salary_rule_id.name == 'Reimbursement Medical') if line.total)}")
            worksheet.write(row, 22,
                            f"{', '.join(f'{line.total:,.2f}' for line in payslip.line_ids.filtered(lambda l: l.salary_rule_id.name == 'Reimbursement Fuel') if line.total)}")
            worksheet.write(row, 23,
                            f"{', '.join(f'{line.total:,.2f}' for line in payslip.line_ids.filtered(lambda l: l.salary_rule_id.name == 'Reimbursement Mobile') if line.total)}")
            worksheet.write(row, 24,
                            f"{', '.join(f'{line.total:,.2f}' for line in payslip.line_ids.filtered(lambda l: l.salary_rule_id.name == 'Reimbursement Certifications') if line.total)}")
            worksheet.write(row, 25,
                            f"{', '.join(f'{line.total:,.2f}' for line in payslip.line_ids.filtered(lambda l: l.salary_rule_id.name == 'Reimbursement Conversion Rate') if line.total)}")
            worksheet.write(row, 26,
                            f"{', '.join(f'{line.total:,.2f}' for line in payslip.line_ids.filtered(lambda l: l.salary_rule_id.name == 'Reimbursement Travel') if line.total)}")
            worksheet.write(row, 27,
                            f"{', '.join(f'{line.total:,.2f}' for line in payslip.line_ids.filtered(lambda l: l.salary_rule_id.name == 'Reimbursement Subscription') if line.total)}")
            worksheet.write(row, 28, '0')  # TODO
            worksheet.write(row, 29,
                            f'{sum(payslip.line_ids.filtered(lambda l: l.category_id.name == "Deduction").mapped("total")):,.2f}')
            worksheet.write(row, 30,
                            f'{((sum(payslip.line_ids.filtered(lambda l: l.category_id.name in ["Allowance", "Basic", "Bonus", "Overtime", "Reimbursement"]).mapped("total")) - sum(payslip.line_ids.filtered(lambda l: l.category_id.name == "Deduction").mapped("total"))) / 100) * 0.25:,.2f}')
            worksheet.write(row, 31,
                            f"{', '.join(f'{line.total:,.2f}' for line in payslip.line_ids.filtered(lambda l: l.salary_rule_id.name == '$10 Bank Charges') if line.total)}")
            worksheet.write(row, 32,
                            f"{', '.join(f'{line.total:,.2f}' for line in payslip.line_ids.filtered(lambda l: l.salary_rule_id.name == 'Net Salary') if line.total)}")
            worksheet.write(row, 33,
                            f"{sum(line.total for line in payslip.line_ids.filtered(lambda l: l.salary_rule_id.name == 'Net Salary') if line.total) / (payslip.payslip_run_id.conversion_rate or 1.0):,.2f}")
            worksheet.write(row, 34, "")
            worksheet.write(row, 35, payslip.employee_id.joining_date.strftime('%d %b %Y') or '')
            worksheet.write(row, 36, payslip.employee_id.bank_account_id.acc_number or '')
            worksheet.write(row, 37, '\n'.join(
                part for part in [
                    f"Title: {payslip.employee_id.bank_account_id.acc_holder_name}" if payslip.employee_id.bank_account_id.acc_holder_name else '',
                    f"IBAN: {payslip.employee_id.bank_account_id.iban}" if payslip.employee_id.bank_account_id.iban else '',
                    f"SWIFT: {payslip.employee_id.bank_account_id.swift}" if payslip.employee_id.bank_account_id.swift else '',
                    f"Code: {payslip.employee_id.bank_account_id.code}" if payslip.employee_id.bank_account_id.code else ''
                ] if part
            ))
            worksheet.write(row, 38, payslip.employee_id.bank_account_id.bank_id.name or '')
            worksheet.write(row, 39, payslip.employee_id.address_home_id.name)

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

    @api.onchange('line_ids.total', 'line_ids.category_id', 'line_ids.salary_rule_id')
    def _compute_wht_uae(self):
        for slip in self:
            salary_with_allowances = slip.contract_id.wage+slip.contract_id.travel_allowances+slip.contract_id.fuel_allowances+slip.contract_id.relocation_allowances-((slip.contract_id.wage+slip.contract_id.travel_allowances+slip.contract_id.fuel_allowances+slip.contract_id.relocation_allowances)/30*slip.worked_days_line_ids.filtered(lambda l:l.work_entry_type_id.name=='Out of Contract').number_of_days)
            overtime = sum(slip.line_ids.filtered(lambda l:l.category_id.name == 'Overtime').mapped('total'))
            input_total = sum(line.amount if line.input_type_id.code not in ['DEDUCTION', 'ATTACH_SALARY'] else -line.amount for line in slip.input_line_ids)

            slip.wht_uae_amount = (salary_with_allowances+overtime+input_total)/100* 0.25

            # TODO: below is old code
            # categories = ['Allowance', 'Basic', 'Bonus', 'Overtime', 'Reimbursement']
            # earnings = sum(
            #     line.total for line in slip.line_ids
            #     if line.category_id and line.category_id.name in categories
            # )
            # deductions = sum(
            #     line.total for line in slip.line_ids
            #     if line.category_id and line.category_id.name == 'Deduction'
            # )
            # slip.wht_uae_amount = ((earnings - deductions) / 100) * 0.25

    def print_payslip_pdf(self):
        return self.env.ref('ws_hr_payroll_entries.action_report_payslip_custom').report_action(self)
