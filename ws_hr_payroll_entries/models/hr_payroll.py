# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError, UserError


class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'


    def _get_available_contracts_domain(self):
        return [('contract_ids.state', 'in', ('open', 'close')), ('company_id', '=', self.env.company.id)]

    def _get_employees(self):
        active_employee_ids = self.env.context.get('active_employee_ids', False)
        if active_employee_ids:
            employees_slip = self.env['hr.employee'].browse(active_employee_ids)
            employees_end = employees_slip.search([('stop_salary','=',False)])
            return employees_end
        # YTI check dates too
        final_emp_list = self.env['hr.employee'].search(self._get_available_contracts_domain())
        final_emp = final_emp_list.search([('stop_salary','=',False)])
        return final_emp


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'


    def compute_sheet(self):
        for payslip in self:
            date_from = str(payslip.date_from)
            month = int(date_from[-5:-3])
            if month == 1 or month == 3 or month == 5 or month == 7 or month == 8 or month == 10 or month == 12:
                days = 31
            elif month == 2:
                days = 28
            else:
                days = 30

            employee_wage = payslip.employee_id.contract_id.wage
            per_day_employee_wage = employee_wage / days

            data=[]
            """Attendance Count"""
            attendances = self.env['hr.attendance'].search([('employee_id','=',payslip.employee_id.id),('att_date','>=',payslip.date_from),('att_date','<=',payslip.date_to)])
            attendance_day=0
            attendance_hours=0
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

            """Leave Count"""
            leaves = self.env['hr.leave'].search([('employee_id','=',payslip.employee_id.id),('date_from','>=',payslip.date_from),('date_to','<=',payslip.date_to),('state','=','validate')])
            leave_day=0

            for lv in leaves:
                leave_day += 1
            lv_end = self.env['hr.work.entry.type'].search([('code','=','LEAVE110')], limit=1)
            data.append((0,0,{
                'payslip_id': payslip.id,
                'work_entry_type_id': lv_end.id,
                'name': lv_end.name,
                'number_of_days':leave_day,
            }))

            """Rest Day Count"""
            day = (payslip.date_to - payslip.date_from).days + 1
            start_date = payslip.date_from
            rest_day_count=0
            for ia in range(day):
                start_date = start_date + timedelta(1)
                attendance_present = self.env['resource.calendar.attendance'].sudo().search([('dayofweek','=',start_date.weekday()),('calendar_id','=',payslip.employee_id.resource_calendar_id.id)], limit=1)
                attendd=self.env['hr.attendance'].search([('employee_id' ,'=', payslip.employee_id.id),('att_date' ,'=', start_date)], limit=1)
                remain_day = 0
                if attendd:
                    remain_day = 1 - attendance_day
                if not attendance_present:
                    rest_day_count+= 1 - remain_day

            rest_day_end = self.env['hr.work.entry.type'].search([('code','=','LEAVE100')], limit=1)
            data.append((0,0,{
                'payslip_id': payslip.id,
                'work_entry_type_id': rest_day_end.id,
                'name': rest_day_end.name,
                'number_of_days':rest_day_count,
            }))

            """Absent Count"""
            total_days = attendance_day  + leave_day + rest_day_count
            absent_day = (day - total_days)
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
