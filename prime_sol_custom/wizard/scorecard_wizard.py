from odoo import api, fields, models, registry, _
from datetime import date, timedelta
from odoo.exceptions import ValidationError

class ScorecardWizard(models.TransientModel):
    _name = "scorecard.wizard"
    _description = 'Scorecard Wizard'

    @api.model
    def default_get(self, default_fields):
        res = super(ScorecardWizard, self).default_get(default_fields)
        today = date.today()

        # First day of the current year
        first_day_current_year = today.replace(month=1, day=1)

        # Yesterday (today - 1 day)
        yesterday = today - timedelta(days=1)

        res.update({
            'date_from': first_day_current_year or False,
            'date_to': today or False
        })
        return res

    date_from = fields.Date(string="Start Date", required=True)
    date_to = fields.Date(string="End Date", required=True)
    partner_id = fields.Many2one('res.partner', string="Company", required=True, domain=[('is_company', '=', True)])

    def action_confirm(self):
        pass