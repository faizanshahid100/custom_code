from email.policy import default
from itertools import count

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ConnectwiseTimesheet(models.Model):
    _name = 'connectwise.timesheet'
    _rec_name = 'employee_id'
    _description = 'ConnectWise Daily Timesheet'
    _order = 'work_date desc'

    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        default=lambda self: self.env.user.employee_id
    )

    work_date = fields.Date(string='Date', required=True)
    total_hours = fields.Float(string='Total Working Hours', default=1)
    billable_hours = fields.Float(
        string='Billable Hours',
        compute='_compute_hours',
        store=True
    )
    non_billable_hours = fields.Float(
        string='Non-Billable Hours',
        compute='_compute_hours',
        store=True
    )
    tickets = fields.Integer(
        string='Tickets',
        compute='_compute_hours',
        store=True
    )
    is_connectwise_admin = fields.Boolean(compute='_compute_is_connectwise_admin')

    line_ids = fields.One2many(
        'connectwise.timesheet.line',
        'timesheet_id',
        string='Timesheet Lines'
    )

    def _compute_is_connectwise_admin(self):
        is_admin = self.env.user.has_group(
            'connectwise_timesheet.group_connectwise_admin'
        )
        for rec in self:
            rec.is_connectwise_admin = is_admin

    def _sync_daily_progress(self, tickets, billable_hours_percentage):
        DailyProgress = self.env['daily.progress']

        for rec in self:
            user = rec.employee_id.user_id
            if not user:
                raise ValidationError(
                    "Employee has no linked user."
                )

            if not rec.total_hours:
                raise ValidationError("Total hours must be greater than zero.")

            vals = {
                'resource_user_id': user.id,
                'avg_resolved_ticket': tickets,
                'billable_hours': billable_hours_percentage,
                'date_of_project': rec.work_date,
                'connectwise_id': rec.id,
            }

            progress = DailyProgress.search(
                [('connectwise_id', '=', rec.id)],
                limit=1
            )

            if progress:
                progress.write(vals)
            else:
                DailyProgress.create(vals)

    @api.depends('line_ids.actual_hours', 'line_ids.ticket')
    def _compute_hours(self):
        for rec in self:
            billable_lines = rec.line_ids.filtered(lambda l: l.ticket != '0 - ')
            non_billable_lines = rec.line_ids.filtered(lambda l: l.ticket == '0 - ')
            rec.billable_hours = sum(billable_lines.mapped('actual_hours'))
            rec.non_billable_hours = sum(non_billable_lines.mapped('actual_hours'))
            rec.tickets = len(billable_lines)

            tickets = len(rec.line_ids.filtered(lambda l: l.ticket != '0 - '))
            billable_hours = sum(billable_lines.mapped('actual_hours'))
            total_hours = sum(rec.line_ids.mapped('actual_hours'))
            billable_percentage = float((billable_hours / total_hours) * 100)
            if tickets and billable_hours:
                rec._sync_daily_progress(tickets, billable_percentage)

    # @api.model
    # def create(self, vals):
    #     record = super().create(vals)
    #     record._sync_daily_progress()
    #     return record

    def write(self, vals):
        res = super().write(vals)
        self._sync_daily_progress()
        return res

class ConnectwiseTimesheetLine(models.Model):
    _name = 'connectwise.timesheet.line'
    _description = 'ConnectWise Timesheet Line'

    timesheet_id = fields.Many2one(
        'connectwise.timesheet',
        string='Timesheet',
        ondelete='cascade',
        required=True
    )

    ticket = fields.Char(string='Ticket')
    internal_ticket = fields.Char(string='Internal Ticket')
    timespan = fields.Char(string='Time Span')
    charge_to = fields.Char(string='Charge To')
    work_role = fields.Char(string='Work Role')
    actual_hours = fields.Float(string='Actual Hours')
    notes = fields.Text(string='Notes')
