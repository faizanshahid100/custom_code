from odoo import models, fields, api
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from collections import defaultdict


class AttendanceActivity(models.Model):
    _name = 'attendance.activity'
    _description = 'Attendance Activity'

    name = fields.Char(string='Name', required=True, translate=True,
                              help='The name of the attendance activity. E.g. Normal Working, Overtime, etc')

    attendance_status_ids = fields.One2many('attendance.state', 'activity_id', string='Attendance Status',
                                            help='The check-in and check-out statuses of this activity')

    status_count = fields.Integer(string='Status Count', compute='_compute_status_count')
    is_attedance_created = fields.Boolean('IS Attendance Created')

    _sql_constraints = [
        ('unique_name',
         'UNIQUE(name)',
         "The Name of the attendance activity must be unique!"),
    ]

    @api.depends('attendance_status_ids')
    def _compute_status_count(self):
        for r in self:
            r.status_count = len(r.attendance_status_ids)

    def getAttendance(self, device_id=None, user_id=None):
        domain = [('attendance_state_id', 'in', self.mapped('attendance_status_ids').ids)]
        if device_id:
            domain += [('device_id', '=', device_id.id)]

        if user_id:
            domain += [('user_id', '=', user_id.id)]

        return self.env['user.attendance'].search(domain)

    def action_attendace_validated(self):
        user_attendance = self.env['user.attendance']
        user_attendance.action_attendance_validated()

    def action_attendance_validated(self):
        month_datetime = fields.Date.today() - timedelta(5)
        for month_date in range(5):
            datetime = month_datetime + timedelta(month_date)
            date_start = datetime + relativedelta(hours=0)
            date_end = datetime + relativedelta(hours=23)
            total_employee = self.env['hr.employee'].search([])
            employee_attendance_map = defaultdict(list)

            for employee in total_employee:
                attendance_test = self.env['user.attendance']
                attendance_list = attendance_test.search([
                    ('employee_id', '=', employee.id),
                    ('timestamp', '>=', date_start),
                    ('timestamp', '<=', date_end),
                    ('is_attedance_created', '=', False)
                ], order="timestamp asc")

                if attendance_list:
                    employee_attendance_map[employee.id].extend(attendance_list)
            for employee_id, attendances in employee_attendance_map.items():
                attendances_sorted = sorted(attendances, key=lambda x: x.timestamp)

                check_ins = [r for r in attendances_sorted if r.attendance_state_id.type == 'checkin']
                check_outs = [r for r in attendances_sorted if r.attendance_state_id.type == 'checkout']
                if check_ins:
                    print(f'check_ins[0].timestamp:{check_ins[0].timestamp}')

                    # Check if there is at least one check-out
                    if check_outs and check_ins[0].timestamp > check_outs[-1].timestamp:
                        # Handle midnight scenario by updating the check-out to the next day
                        next_day_check_outs = [co for co in check_outs if co.timestamp >= check_ins[0].timestamp]
                        if next_day_check_outs:
                            check_outs[-1] = next_day_check_outs[-1]

                    existing_attendance = self.env['hr.attendance'].search([
                        ('employee_id', '=', employee_id),
                        ('check_in', '<=', check_ins[0].timestamp),
                        ('check_out', '=', False)
                    ], order="check_in desc", limit=1)

                    if existing_attendance:
                        if check_outs:
                            existing_attendance.write({'check_out': check_outs[-1].timestamp})
                        for attendance in attendances_sorted:
                            attendance.write({'is_attedance_created': True})
                    else:
                        if check_outs and check_ins[0].timestamp <= check_outs[-1].timestamp:
                            vals = {
                                'employee_id': employee_id,
                                'check_in': check_ins[0].timestamp,
                                'check_out': check_outs[-1].timestamp,
                            }
                            hr_attendance = self.env['hr.attendance'].create(vals)
                            for attendance in attendances_sorted:
                                attendance.write({'is_attedance_created': True})
                        else:
                            # Log or handle the scenario where the check-out is earlier than the check-in
                            pass
