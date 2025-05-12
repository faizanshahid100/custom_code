from odoo import models, fields, api
from datetime import datetime, timedelta
from pytz import timezone


class EmployeeDashboardLine(models.Model):
    _name = 'employee.dashboard.line'
    _description = 'Employee Dashboard Line'
    _order = 'department_id'

    department_id = fields.Many2one('hr.department', string='Department', required=True, ondelete='cascade')
    current_count = fields.Integer(string='Employees Today')
    last_week_count = fields.Integer(string='1 Week Ago')
    two_weeks_count = fields.Integer(string='2 Weeks Ago')
    snapshot_date = fields.Date(string="Snapshot Date", default=fields.Date.today)
    show_in_view = fields.Boolean(compute='_compute_show_in_view', store=True)

    @api.model
    def _update_snapshots(self):
        """Ensure every department has a dashboard record, and update counts."""
        # Get current date in Pakistan timezone
        pakistan_tz = timezone('Asia/Karachi')
        today = datetime.now(pakistan_tz).date()
        one_week_ago = today - timedelta(weeks=1)
        two_weeks_ago = today - timedelta(weeks=2)

        all_depts = self.env['hr.department'].search([])
        existing_lines = self.search([]).mapped('department_id')

        for dept in all_depts:
            # Get employee counts
            current = self.env['hr.employee'].search_count([
                ('department_id', '=', dept.id),
                ('joining_date', '<=', today)
            ])
            last_week = self.env['hr.employee'].search_count([
                ('department_id', '=', dept.id),
                ('joining_date', '<=', one_week_ago)
            ])
            two_weeks = self.env['hr.employee'].search_count([
                ('department_id', '=', dept.id),
                ('joining_date', '<=', two_weeks_ago)
            ])

            # Update or create dashboard line
            dashboard_line = self.search([('department_id', '=', dept.id)], limit=1)
            if dashboard_line:
                dashboard_line.write({
                    'current_count': current,
                    'last_week_count': last_week,
                    'two_weeks_count': two_weeks,
                    'snapshot_date': today,
                })
            else:
                self.create({
                    'department_id': dept.id,
                    'current_count': current,
                    'last_week_count': last_week,
                    'two_weeks_count': two_weeks,
                    'snapshot_date': today,
                })

        # Remove dashboard lines for departments that no longer exist
        removed_lines = self.search([('department_id', 'not in', all_depts.ids)])
        removed_lines.unlink()

    @api.depends('current_count', 'last_week_count', 'two_weeks_count', 'department_id')
    def _compute_show_in_view(self):
        for rec in self:
            # Show only if at least one of the counts is non-zero
            rec.show_in_view = not (
                    rec.current_count == 0 and
                    rec.last_week_count == 0 and
                    rec.two_weeks_count == 0
            )

class HrDepartment(models.Model):
    _inherit = 'hr.department'

    @api.model
    def create(self, vals):
        record = super().create(vals)
        self.env['employee.dashboard.line']._update_snapshots()
        return record

    def write(self, vals):
        result = super().write(vals)
        self.env['employee.dashboard.line']._update_snapshots()
        return result

    def unlink(self):
        result = super().unlink()
        self.env['employee.dashboard.line']._update_snapshots()
        return result


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.model
    def create(self, vals):
        record = super().create(vals)
        self.env['employee.dashboard.line']._update_snapshots()
        return record

    def write(self, vals):
        result = super().write(vals)
        self.env['employee.dashboard.line']._update_snapshots()
        return result

    def unlink(self):
        result = super().unlink()
        self.env['employee.dashboard.line']._update_snapshots()
        return result
