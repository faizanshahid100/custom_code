from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ScoreWeightage(models.Model):
    _name = "score.weightage"
    _description = 'Score Weightage'

    name = fields.Char()
    is_active = fields.Boolean(string='Is Active')
    feedback = fields.Float(string='Feedback')
    survey = fields.Float(string='Survey')
    kpi = fields.Float(string='KPI')
    weekly_meeting = fields.Float(string='Weekly Meeting')
    daily_attendance = fields.Float(string='Daily Attendance')
    office_coming = fields.Float(string='Office Coming')

    @api.constrains('is_active')
    def _check_unique_active(self):
        if self.is_active and self.search_count([('is_active', '=', True)]) > 1:
            raise ValidationError('Only one record can be active at a time.')

    @api.constrains('feedback', 'survey', 'kpi', 'weekly_meeting', 'daily_attendance', 'office_coming')
    def _check_total_percentage(self):
        for record in self:
            total = record.feedback + record.survey + record.kpi + record.weekly_meeting + record.daily_attendance + record.office_coming
            if total != 100:
                raise ValidationError(f'The total weightage of all Weightage must equal 100%. Currently, it sums to {total}.')