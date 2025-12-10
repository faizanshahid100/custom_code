from odoo import models, fields, api

class SurveySurveyExt(models.Model):
    _inherit = 'survey.survey'

    is_client_feedback = fields.Boolean(string="Is Client Feedback")

    def action_export_excel(self):
        """Open wizard to export survey responses to Excel"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Export Survey to Excel',
            'res_model': 'survey.excel.export',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_survey_id': self.id}
        }