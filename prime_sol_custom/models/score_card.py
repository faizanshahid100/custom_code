from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ScoreCard(models.Model):
    _name = "score.card"
    _description = 'Score Card'

    date_from = fields.Date('Date From')
    date_to = fields.Date('Date To')
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

    def name_get(self):
        result = []
        for rec in self:
            employee = rec.employee_id.name or ''
            date_from = rec.date_from.strftime('%d-%b-%Y') if rec.date_from else 'N/A'
            date_to = rec.date_to.strftime('%d-%b-%Y') if rec.date_to else 'N/A'
            name = f"{employee} ({date_from} - {date_to})"
            result.append((rec.id, name))
        return result

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
        for record in self:
            active_weightage = self.env['score.weightage'].search([('is_active', '=', True), ('partner_id', '=', record.employee_id.contractor.id), ('department_id', '=', record.employee_id.department_id.id)])[0]
            if not active_weightage:
                raise ValidationError(f'No Weightage Available for **{record.employee_id.department_id.name}** Department')
            record.cumulative_score = (
                    (record.feedback * active_weightage.feedback / 100) +
                    (record.survey * active_weightage.survey / 100) +
                    (record.kpi * active_weightage.kpi / 100) +
                    (record.weekly_meeting * active_weightage.weekly_meeting / 100) +
                    (record.daily_attendance * active_weightage.daily_attendance / 100) +
                    (record.office_coming * active_weightage.office_coming / 100)
            )
            record.department_id = record.employee_id.department_id.id

    def action_view_feedback(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Feedback Details',
            'view_mode': 'tree',
            'res_model': 'hr.employee.feedback',
            'domain': [('employee_id', '=', self.employee_id.id), ('date_feedback', '>=', self.date_from), ('date_feedback', '<=', self.date_to)],
            'target': 'current',
            'help': _(
                '<p class="o_view_nocontent_smiling_face">'
                '<b>No feedback received.</b><br/>'
                'No news is good news — congratulations, you scored 100%!'
                '</p>'
            )
        }
    def action_view_survey(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Survey Details',
            'view_mode': 'tree,form',
            'res_model': 'survey.user_input',
            'domain': [('employee_id', '=', self.employee_id.id), ('survey_id.title', '=', '2025: Employee Performance Feedback'), ('test_entry', '=', False), ('create_date', '>=', self.date_from),
                       ('create_date', '<=', self.date_to)],
            'target': 'current',
            'help': _(
                '<p class="o_view_nocontent_smiling_face">'
                '<b>No survey records found.</b><br/>'
                'Please reach out to your line manager for further details.'
                '</p>'
            )
        }
    def action_view_kpi(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'KPI Details',
            'view_mode': 'tree,form',
            'res_model': 'daily.progress',
            'domain': [('resource_user_id.employee_id', '=', self.employee_id.id), ('date_of_project', '>=', self.date_from),
                       ('date_of_project', '<=', self.date_to)],
            'target': 'current',
        }

    def action_view_weekly_meeting(self):
        tree_view_id = self.env.ref('prime_sol_custom.view_meeting_details_tree').id
        return {
            'type': 'ir.actions.act_window',
            'name': 'Weekly Meeting Details',
            'view_mode': 'tree',
            'res_model': 'meeting.details',
            'domain': [
                ('employee_id', '=', self.employee_id.id),
                ('meeting_id.date', '>=', self.date_from),
                ('meeting_id.date', '<=', self.date_to)
            ],
            'views': [(tree_view_id, 'tree')],
            'target': 'current',
        }
    def action_view_attendance(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Attendance Details',
            'view_mode': 'tree',
            'res_model': 'hr.attendance',
            'domain': [('employee_id', '=', self.employee_id.id),
                       ('check_in', '>=', self.date_from),
                       ('check_in', '<=', self.date_to)],
            'target': 'current',
        }