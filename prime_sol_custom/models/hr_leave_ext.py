# -*- coding: utf-8 -*-
import logging
import pytz

from collections import namedtuple, defaultdict

from datetime import datetime, timedelta, time
from pytz import timezone, UTC
from odoo.tools import date_utils

from odoo import api, Command, fields, models, tools
from odoo.addons.base.models.res_partner import _tz_get
from odoo.addons.resource.models.resource import float_to_time, HOURS_PER_DAY
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_compare, format_date
from odoo.tools.float_utils import float_round
from odoo.tools.misc import format_date
from odoo.tools.translate import _
from odoo.osv import expression

_logger = logging.getLogger(__name__)


class HolidaysRequestExt(models.Model):
    _inherit = 'hr.leave'

    def action_validate(self):
        current_employee = self.env.user.employee_id
        leaves = self._get_leaves_on_public_holiday()
        if leaves:
            raise ValidationError(
                _('The following employees are not supposed to work during that period:\n %s') % ','.join(
                    leaves.mapped('employee_id.name')))

        if any(holiday.state not in ['confirm', 'validate1'] and holiday.validation_type != 'no_validation' for holiday
               in self):
            raise UserError(_('Time off request must be confirmed in order to approve it.'))

        self.write({'state': 'validate'})

        leaves_second_approver = self.env['hr.leave']
        leaves_first_approver = self.env['hr.leave']

        for leave in self:
            if leave.validation_type == 'both':
                leaves_second_approver += leave
            else:
                leaves_first_approver += leave

            if leave.holiday_type == 'employee' and leave.state == 'validate':
                for employee in leave.employee_ids:
                    check_in_date = leave.request_date_from
                    check_out_time_offset = timedelta(hours=8)  # Shift duration (2 PM - 10 PM)

                    while check_in_date <= leave.request_date_to:
                        if check_in_date.weekday() not in [5, 6]:  # Skip Saturday (5) & Sunday (6)
                            check_in_time = datetime.combine(check_in_date, datetime.min.time()) + timedelta(
                                hours=9)  # 2 PM
                            check_out_time = check_in_time + check_out_time_offset  # 10 PM

                            self.env['hr.attendance'].create({
                                'employee_id': employee.id,
                                'check_in': check_in_time,
                                'check_out': check_out_time,
                            })

                        check_in_date += timedelta(days=1)  # Move to the next day

        leaves_second_approver.write({'second_approver_id': current_employee.id})
        leaves_first_approver.write({'first_approver_id': current_employee.id})

        employee_requests = self.filtered(lambda hol: hol.holiday_type == 'employee')
        employee_requests._validate_leave_request()
        if not self.env.context.get('leave_fast_create'):
            employee_requests.filtered(lambda holiday: holiday.validation_type != 'no_validation').activity_update()

        return True

    def action_refuse(self):
        # Call the original action_refuse() logic using super()
        result = super().action_refuse()

        # Delete attendance records for the refused leave period (excluding weekends)
        for holiday in self:
            for employee in holiday.employee_ids:
                attendance_records = self.env['hr.attendance'].search([
                    ('employee_id', '=', employee.id),
                    ('check_in', '>=', holiday.request_date_from),
                    ('check_out', '<=', holiday.request_date_to),
                ])

                for attendance in attendance_records:
                    if attendance.check_in.weekday() not in [5, 6]:  # Skip Saturday & Sunday
                        attendance.unlink()

        return result

