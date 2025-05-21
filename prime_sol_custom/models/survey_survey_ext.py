from odoo import models, fields

class SurveySurveyExt(models.Model):
    _inherit = 'survey.survey'

    is_client_feedback = fields.Boolean(string="Is Client Feedback")