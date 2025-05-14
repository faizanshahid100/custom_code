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

