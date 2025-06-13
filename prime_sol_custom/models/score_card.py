from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ScoreCard(models.Model):
    _name = "score.card"
    _description = 'Score Card'

    employee_id = fields.Many2one('hr.employee', string="Employee")
    partner_id = fields.Many2one('res.partner', string="Company", domain="[('is_company','=', True)]")
    department_id = fields.Many2one('hr.department', string='🏢 Department')
    feedback = fields.Float(string="Feedback (%)")
    survey = fields.Float(string="Survey (%)")
    kpi = fields.Float(string="KPI (%)")
    weekly_meeting = fields.Float(string="Weekly Meeting (%)")
    daily_attendance = fields.Float(string="Daily Attendance (%)")
    office_coming = fields.Float(string="Office Coming (%)")
    cumulative_score = fields.Float('Cumulative Score', compute='_compute_cumulative_score', digits=(16, 4), store=True)
    # Computed fields for pivot (in actual %)
    feedback_pivot = fields.Float(string="Feedback", compute='_compute_pivot_percentages', store=True)
    survey_pivot = fields.Float(string="Survey", compute='_compute_pivot_percentages', store=True)
    kpi_pivot = fields.Float(string="KPI", compute='_compute_pivot_percentages', store=True)
    weekly_meeting_pivot = fields.Float(string="Weekly Meeting", compute='_compute_pivot_percentages',
                                        store=True)
    daily_attendance_pivot = fields.Float(string="Daily Attendance", compute='_compute_pivot_percentages',
                                          store=True)
    office_coming_pivot = fields.Float(string="Office Coming", compute='_compute_pivot_percentages', store=True)
    cumulative_score_pivot = fields.Float(string="Cumulative Score", compute='_compute_pivot_percentages',
                                          store=True)

    @api.depends(
        'feedback', 'survey', 'kpi', 'weekly_meeting',
        'daily_attendance', 'office_coming', 'cumulative_score'
    )
    def _compute_pivot_percentages(self):
        for rec in self:
            rec.feedback_pivot = rec.feedback * 100
            rec.survey_pivot = rec.survey * 100
            rec.kpi_pivot = rec.kpi * 100
            rec.weekly_meeting_pivot = rec.weekly_meeting * 100
            rec.daily_attendance_pivot = rec.daily_attendance * 100
            rec.office_coming_pivot = rec.office_coming * 100
            rec.cumulative_score_pivot = rec.cumulative_score * 100

    @api.depends('feedback', 'survey', 'kpi', 'weekly_meeting', 'daily_attendance', 'office_coming')
    def _compute_cumulative_score(self):
        active_weightage = self.env['score.weightage'].search([('is_active', '=', True), ('partner_id', '=', self.partner_id.id), ('department_id', '=', self.department_id.id)])
        if not active_weightage:
            raise ValidationError('No Weightage Available regarding the parameter')
        for record in self:
            record.cumulative_score = (
                    (record.feedback * active_weightage.feedback / 100) +
                    (record.survey * active_weightage.survey / 100) +
                    (record.kpi * active_weightage.kpi / 100) +
                    (record.weekly_meeting * active_weightage.weekly_meeting / 100) +
                    (record.daily_attendance * active_weightage.daily_attendance / 100) +
                    (record.office_coming * active_weightage.office_coming / 100)
            )
            record.department_id = record.employee_id.department_id.id

