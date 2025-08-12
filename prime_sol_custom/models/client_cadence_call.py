from odoo import models, fields, api

class ClientCadenceCall(models.Model):
    _name = "client.cadence.call"
    _rec_name = "partner_id"
    _description = "Client Cadence Call Schedule"
    _order = "id"

    partner_id = fields.Many2one('res.partner',"Client (Company)", domain=[('is_company', '=', True)])
    manager_contractor = fields.Char("Manager (Contractor)")
    meeting_schedule = fields.Char("Meeting Schedule")
    frequency = fields.Selection([
        ('weekly', 'Weekly'),
        ('bi_monthly', 'Bi-monthly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('other', 'Other')
    ], string="Frequency")
    recurring_invite = fields.Selection([
        ('y', 'Y'),
        ('n', 'N')
    ], string="With Recurring Invite Y/N")
    notes = fields.Text("Notes")
