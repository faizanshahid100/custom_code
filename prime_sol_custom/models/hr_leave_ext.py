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


class HrLeaveExt(models.Model):
    _inherit = 'hr.leave'

    # def action_validate(self):
    #     current_employee = self.env.user.employee_id
    #     leaves = self._get_leaves_on_public_holiday()
    #     if leaves:
    #         raise ValidationError(
    #             _('The following employees are not supposed to work during that period:\n %s') % ','.join(
    #                 leaves.mapped('employee_id.name')))
    #
    #     if any(holiday.state not in ['confirm', 'validate1'] and holiday.validation_type != 'no_validation' for holiday
    #            in self):
    #         raise UserError(_('Time off request must be confirmed in order to approve it.'))
    #
    #     self.write({'state': 'validate'})
    #
    #     leaves_second_approver = self.env['hr.leave']
    #     leaves_first_approver = self.env['hr.leave']
    #
    #     for leave in self:
    #         if leave.validation_type == 'both':
    #             leaves_second_approver += leave
    #         else:
    #             leaves_first_approver += leave
    #
    #         if leave.holiday_type == 'employee' and leave.state == 'validate':
    #             for employee in leave.employee_ids:
    #                 check_in_date = leave.request_date_from
    #                 check_out_time_offset = timedelta(hours=8)  # Shift duration (2 PM - 10 PM)
    #
    #                 while check_in_date <= leave.request_date_to:
    #                     if check_in_date.weekday() not in [5, 6]:  # Skip Saturday (5) & Sunday (6)
    #                         check_in_time = datetime.combine(check_in_date, datetime.min.time()) + timedelta(
    #                             hours=9)  # 2 PM
    #                         check_out_time = check_in_time + check_out_time_offset  # 10 PM
    #
    #                         self.env['hr.attendance'].create({
    #                             'employee_id': employee.id,
    #                             'check_in': check_in_time,
    #                             'check_out': check_out_time,
    #                         })
    #
    #                     check_in_date += timedelta(days=1)  # Move to the next day
    #
    #     leaves_second_approver.write({'second_approver_id': current_employee.id})
    #     leaves_first_approver.write({'first_approver_id': current_employee.id})
    #
    #     employee_requests = self.filtered(lambda hol: hol.holiday_type == 'employee')
    #     employee_requests._validate_leave_request()
    #     if not self.env.context.get('leave_fast_create'):
    #         employee_requests.filtered(lambda holiday: holiday.validation_type != 'no_validation').activity_update()
    #
    #     return True
    #
    # def action_refuse(self):
    #     # Call the original action_refuse() logic using super()
    #     result = super().action_refuse()
    #
    #     # Delete attendance records for the refused leave period (excluding weekends)
    #     for holiday in self:
    #         for employee in holiday.employee_ids:
    #             attendance_records = self.env['hr.attendance'].search([
    #                 ('employee_id', '=', employee.id),
    #                 ('check_in', '>=', holiday.request_date_from),
    #                 ('check_out', '<=', holiday.request_date_to),
    #             ])
    #
    #             for attendance in attendance_records:
    #                 if attendance.check_in.weekday() not in [5, 6]:  # Skip Saturday & Sunday
    #                     attendance.unlink()
    #
    #     return result

    @api.model
    def create(self, vals):
        record = super(HrLeaveExt, self).create(vals)

        # Prepare email values
        employee = record.employee_id
        department = employee.department_id.name or "N/A"
        contractor = employee.contractor.name if hasattr(employee, 'contractor') else "N/A"

        # Convert date fields to dd-mm-YYYY
        date_from = ""
        date_to = ""

        if record.request_date_from:
            date_from = fields.Date.to_date(record.request_date_from).strftime("%d-%m-%Y")

        if record.request_date_to:
            date_to = fields.Date.to_date(record.request_date_to).strftime("%d-%m-%Y")

        # Email recipient
        to_email = "myle.gruet@primesystemsolutions.com,ashar.muzaffar@primesystemsolutions.com"

        # Email subject
        subject = f"Leave Request Submitted - {employee.name}"

        # Email body (HTML)
        body = f"""
                <p><b>Hi,</b></p>
                <p><b>{employee.name}</b> has applied for leave.</p>

                <p><b>Employee Name:</b> {employee.name}</p>
                <p><b>Department:</b> {department}</p>
                <p><b>Company:</b> {contractor}</p>
                <p><b>Leave From:</b> {date_from}</p>
                <p><b>Leave To:</b> {date_to}</p>
            """

        # Send email
        mail_values = {
            "subject": subject,
            "body_html": body,
            "email_to": to_email,
            "auto_delete": False,
        }
        self.env['mail.mail'].sudo().create(mail_values).send()

        return record

    # @api.constrains('request_date_from', 'request_date_to', 'holiday_status_id')
    # def _check_leave_constraints(self):
    #     today = fields.Date.today()
    #
    #     for leave in self:
    #         employee = leave.employee_id
    #         leave_type = leave.holiday_status_id.name.strip().lower()
    #
    #         if not leave.request_date_from or not leave.request_date_to:
    #             continue
    #
    #         # PK Parental Leaves
    #         if leave_type == 'pk parental leaves':
    #             if employee.gender == 'male' and leave.number_of_days_display > 3:
    #                 raise ValidationError(_("Paternity Leaves cannot exceed 3 days."))
    #
    #             if employee.gender == 'female':
    #                 if leave.number_of_days_display > 45:
    #                     raise ValidationError(_("Maternity Leaves cannot exceed 45 days."))
    #
    #                 if employee.joining_date and (leave.request_date_from - employee.joining_date).days < 180:
    #                     raise ValidationError(
    #                         _("Employee must have completed 6 months of service for Maternity Leave.")
    #                     )
    #
    #         # Standard Time-Off (ERP Manager exemption applies ONLY here)
    #         elif leave_type == 'standard time-off':
    #
    #             # ERP Manager → no restriction
    #             if self.env.user.has_group('base.group_erp_manager'):
    #                 continue
    #
    #             # 1️⃣ Single-day leave → 48 hours before or after
    #             if leave.number_of_days_display == 1:
    #                 allowed_last_date = leave.request_date_from + timedelta(days=2)
    #
    #                 if today > allowed_last_date:
    #                     raise ValidationError(
    #                         _("Single-day leave must be applied before or within 48 hours after availing the leave.")
    #                     )
    #
    #             # 2️⃣ More than 1 day → 2 weeks in advance
    #             elif leave.number_of_days_display > 1 and (leave.request_date_from - today).days < 14:
    #                 raise ValidationError(
    #                     _("More than 1 day leave must be applied at least 2 weeks in advance.")
    #                 )
    #
    #         # Bereavement Leaves
    #         elif leave_type == 'bereavement leaves':
    #             if leave.number_of_days_display > 3:
    #                 raise ValidationError(_("Bereavement Leaves cannot exceed 3 days."))

    def action_approve(self):
        res = super(HrLeaveExt, self).action_approve()

        for leave in self:
            leave._send_approval_notification_email()

        return res

    def _send_approval_notification_email(self):
        template = self.env.ref('prime_sol_custom.leave_approval_email_template', raise_if_not_found=False)
        recipient_email = 'myle.gruet@primesystemsolutions.com,ashar.muzaffar@primesystemsolutions.com'

        if not template:
            raise UserError("Email template 'leave_approval_email_template' not found.")

        # Force send to the static email
        template.email_to = recipient_email
        template.send_mail(self.id, force_send=True)
