from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ScoreWeightage(models.Model):
    _name = "score.weightage"
    _description = 'Score Weightage'

    name = fields.Char()
    partner_id = fields.Many2one('res.partner', string="Company", domain="[('is_company','=', True)]")
    department_id = fields.Many2one('hr.department', strint='Department')
    is_active = fields.Boolean(string='Is Active')
    feedback = fields.Float(string='Feedback')
    survey = fields.Float(string='Survey')
    kpi = fields.Float(string='KPI')
    weekly_meeting = fields.Float(string='Weekly Meeting')
    daily_attendance = fields.Float(string='Daily Attendance')
    office_coming = fields.Float(string='Office Coming')

    @api.constrains('is_active', 'department_id', 'partner_id')
    def _check_unique_active(self):
        for record in self:
            if record.is_active:
                count = self.search_count([
                    ('is_active', '=', True),
                    ('department_id', '=', record.department_id.id),
                    ('partner_id', '=', record.partner_id.id),
                    ('id', '!=', record.id)  # Exclude the current record
                ])
                if count > 0:
                    raise ValidationError('Only one active record is allowed per Company/department.')

    @api.constrains('feedback', 'survey', 'kpi', 'weekly_meeting', 'daily_attendance', 'office_coming')
    def _check_total_percentage(self):
        for record in self:
            total = record.feedback + record.survey + record.kpi + record.weekly_meeting + record.daily_attendance + record.office_coming
            if total != 100:
                raise ValidationError(f'The total weightage of all Weightage must equal 100%. Currently, it sums to {total}.')