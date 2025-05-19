from odoo import models, fields, api, _

class ScoreCard(models.Model):
    _name = "score.card"
    _description = 'Score Card'

    employee_id = fields.Many2one('hr.employee', string="Employee")
    partner_id = fields.Many2one('res.partner', string="Company", domain="[('is_company','=', True)]")
    feedback = fields.Float(string="Feedback (%)")
    survey = fields.Float(string="Survey (%)")
    kpi = fields.Float(string="KPI (%)")
    weekly_meeting = fields.Float(string="Weekly Meeting (%)")
    daily_attendance = fields.Float(string="Daily Attendance (%)")
    office_coming = fields.Float(string="Office Coming (%)")
    cumulative_score = fields.Float('Cumulative Score', compute='_compute_cumulative_score', store=True)

    @api.depends('feedback', 'survey', 'kpi', 'weekly_meeting', 'daily_attendance', 'office_coming')
    def _compute_cumulative_score(self):
        active_weightage = self.env['score.weightage'].search([('is_active', '=', True)], limit=1)
        if active_weightage:
            for record in self:
                record.cumulative_score = (
                        (record.feedback * active_weightage.feedback / 100) +
                        (record.survey * active_weightage.survey / 100) +
                        (record.kpi * active_weightage.kpi / 100) +
                        (record.weekly_meeting * active_weightage.weekly_meeting / 100) +
                        (record.daily_attendance * active_weightage.daily_attendance / 100) +
                        (record.office_coming * active_weightage.office_coming / 100)
                )

