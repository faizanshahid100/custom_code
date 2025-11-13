from odoo import api, fields, models


class CSMHandbook(models.Model):
    _name ='csm.handbook'


    # name = fields.Char(string='')
    manager_id = fields.Many2one('res.partner', string='Manager')
    customer_id = fields.Many2one('res.partner', string='Customer', domain=[('is_company', '=', True)])
    manager_email = fields.Char(string='Email Address', compute='_compute_manager_fields', store=True, readonly=False)
    # suggested_meeting_frequency = fields.Selection([
    #     ('monthly', 'Monthly'),
    #     ('bi_monthly', 'Bi-Monthly'),
    #     ('weekly', 'Weekly'),
    #     ('bi_weekly', 'Bi-Weekly'),
    #     ('no', 'Not Required')
    # ], string='Suggested Meeting Frequency')
    current_meeting_frequency = fields.Selection([
        ('monthly', 'Monthly'),
        ('bi_monthly', 'Bi-Monthly'),
        ('weekly', 'Weekly'),
        ('bi_weekly', 'Bi-Weekly'),
        ('tbd', 'TBD'),
        ('not_required', 'Not Required')
    ], string='Current Meeting Frequency', compute='_compute_manager_fields', store=True, readonly=False)
    month = fields.Date(string='Month')
    current_month_schedule = fields.Date(string='Current Month Schedule')
    client_attend_call = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
        ('no', 'To Send ff-up'),
        ('not_required', 'Not Required')
    ], string='Client Attended the Call?')
    business_tech = fields.Char(string='Business/Tech', compute='_compute_manager_fields', store=True, readonly=False)
    gar = fields.Selection([
        ('green', 'Green'),
        ('amber', 'Amber'),
        ('red', 'Red'),
    ], string='GAR')
    # gar_comment = fields.Char(string='Comment based on GAR')
    action_amber_red = fields.Html(string='Action steps in Line with the Amber and Red Reason')
    notes = fields.Html(string='Notes')

    @api.depends('manager_id.email', 'manager_id.business_tech', 'manager_id.current_meeting_frequency')
    def _compute_manager_fields(self):
        """Compute all dependent manager-related fields."""
        for record in self:
            manager = record.manager_id
            record.manager_email = manager.email or False
            record.business_tech = manager.business_tech or False
            record.current_meeting_frequency = manager.current_meeting_frequency or False

    @api.depends('gar')
    def _compute_gar_banner(self):
        """Set banner text and color based on GAR value."""
        for record in self:
            if record.gar == 'green':
                record.gar_banner_text = 'GAR: GREEN - Everything is on track!'
                record.gar_banner_color = 'success'
            elif record.gar == 'amber':
                record.gar_banner_text = 'GAR: AMBER - Attention needed!'
                record.gar_banner_color = 'warning'
            elif record.gar == 'red':
                record.gar_banner_text = 'GAR: RED - Critical issues detected!'
                record.gar_banner_color = 'danger'
            else:
                record.gar_banner_text = False
                record.gar_banner_color = False
