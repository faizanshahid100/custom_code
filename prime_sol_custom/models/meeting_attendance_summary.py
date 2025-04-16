from odoo import models, fields, api, _

class MeetingAttendanceSummary(models.Model):
    _name = 'meeting.attendance.summary'
    _description = 'Meeting Attendance Summary'

    employee_id = fields.Many2one('hr.employee', string="Employee")
    partner_id = fields.Many2one('res.partner', string="Company", domain="[('is_company','=', True)]")
    level = fields.Char(string="Level")
    kpi_measurement = fields.Selection([('na', 'N/A' ), ('billable', 'Billable'), ('kpi', 'KPI')], string="KPI Measurement")
    job_id = fields.Many2one('hr.job', string="Designation")
    total_meetings = fields.Integer()
    attended_meetings = fields.Integer()  # Corrected spelling: 'attended_meetings'
    summary_meeting = fields.Float(compute="_compute_summary_meetings",
                                   store=True)  # Corrected function name to '_compute_summary_meetings'

    @api.depends('total_meetings', 'attended_meetings')  # Corrected dependency to 'attended_meetings'
    def _compute_summary_meetings(self):  # Corrected function name to '_compute_summary_meetings'
        for record in self:
            if record.attended_meetings:
                record.summary_meeting = (record.attended_meetings / record.total_meetings)
            else:
                record.summary_meeting = 0.0  # Prevent division by zero