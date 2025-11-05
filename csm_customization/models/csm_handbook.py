from odoo import api, fields, models


class CSMHandbook(models.Model):
    _name ='csm.handbook'


    name = fields.Char(string='')
    manager_id = fields.Many2one('res.partner', string='Manager')
    customer_id = fields.Many2one('res.partner', string='Customer')
    manager_email = fields.Char(related='manager_id.email', string='Email Address')
    suggested_meeting_frequency = fields.Selection([
        ('monthly', 'Monthly'),
        ('bi_monthly', 'Bi-Monthly'),
        ('weekly', 'Weekly'),
        ('bi_weekly', 'Bi-Weekly'),
        ('no', 'Not Required')
    ], string='Suggested Meeting Frequency')
    current_meeting_frequency = fields.Selection([
        ('monthly', 'Monthly'),
        ('bi_monthly', 'Bi-Monthly'),
        ('weekly', 'Weekly'),
        ('bi_weekly', 'Bi-Weekly'),
        ('tbd', 'TBD'),
        ('not_required', 'Not Required')
    ], string='Suggested Meeting Frequency')
    month = fields.Date(string='Month')
    client_attend_call = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
        ('no', 'To Send ff-up'),
        ('not_required', 'Not Required')
    ], string='Client Attended the Call?')
    business_tech = fields.Char(string='Business/Tech')
    gar = fields.Selection([
        ('green', 'Green'),
        ('amber', 'Amber'),
        ('red', 'Red'),
        ('tbd', 'TBD'),
    ], string='GAR')
    gar_comment = fields.Char(string='Comment based on GAR')
    action_amber_red = fields.Html(string='Action steps in Line with the Amber and Red Reason')
    notes = fields.Html(string='Notes')