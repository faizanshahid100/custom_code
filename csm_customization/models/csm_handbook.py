from odoo import api, fields, models


class CSMHandbook(models.Model):
    _name ='csm.handbook'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = 'customer_id'


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
    current_month_schedule = fields.Datetime(string='Current Month Schedule')
    calendar_event_id = fields.Many2one('calendar.event', string='Calendar Event')
    calendar_event_count = fields.Integer(compute='_compute_calendar_event_count')
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
    task_assign_line_ids = fields.One2many('csm.task.lines', 'handbook_id', string='Task Assignment Lines')
    is_meeting_done = fields.Boolean(string='Is Meeting Done?')
    is_meeting_rescheduled = fields.Boolean(string='Is Meeting Rescheduled?')

    @api.depends('calendar_event_id')
    def _compute_calendar_event_count(self):
        for record in self:
            record.calendar_event_count = 1 if record.calendar_event_id else 0

    @api.model
    def create(self, vals):
        record = super().create(vals)
        if record.current_month_schedule:
            record._create_calendar_event()
        return record

    def write(self, vals):
        result = super().write(vals)
        if 'current_month_schedule' in vals or 'manager_id' in vals:
            for record in self:
                if record.calendar_event_id and record.current_month_schedule:
                    event_vals = {
                        'start': record.current_month_schedule,
                        'stop': record.current_month_schedule,
                    }
                    if 'manager_id' in vals and record.manager_id:
                        # Add manager and current user as attendees
                        attendee_ids = [record.manager_id.id]
                        if record.env.user.partner_id.id != record.manager_id.id:
                            attendee_ids.append(record.env.user.partner_id.id)
                        
                        event_vals.update({
                            'name': f'CSM Meeting With {record.manager_id.name} from {record.customer_id.name}',
                            'partner_ids': [(6, 0, attendee_ids)],
                        })
                    record.calendar_event_id.write(event_vals)
                elif record.current_month_schedule and not record.calendar_event_id:
                    record._create_calendar_event()
        return result

    def _create_calendar_event(self):
        if self.current_month_schedule and self.manager_id and self.customer_id:
            # Find or create 10-minute alarm
            alarm = self.env['calendar.alarm'].search([('duration_minutes', '=', 10)], limit=1)
            if not alarm:
                alarm = self.env['calendar.alarm'].create({
                    'name': '10 minutes before',
                    'alarm_type': 'notification',
                    'duration': 10,
                    'interval': 'minutes',
                    'duration_minutes': 10,
                })
            
            # Add manager and current user as attendees
            attendee_ids = [self.manager_id.id]
            if self.env.user.partner_id.id != self.manager_id.id:
                attendee_ids.append(self.env.user.partner_id.id)
            
            event = self.env['calendar.event'].create({
                'name': f'CSM Meeting With {self.manager_id.name} from {self.customer_id.name}',
                'start': self.current_month_schedule,
                'stop': self.current_month_schedule,
                'alarm_ids': [(6, 0, [alarm.id])],
                'csm_handbook_id': self.id,
                'partner_ids': [(6, 0, attendee_ids)],
            })
            self.calendar_event_id = event.id

    def action_view_calendar_event(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Calendar Event',
            'res_model': 'calendar.event',
            'res_id': self.calendar_event_id.id,
            'view_mode': 'form',
            'target': 'current',
        }


    @api.depends('manager_id.email', 'manager_id.business_tech', 'manager_id.current_meeting_frequency')
    def _compute_manager_fields(self):
        """Compute all dependent manager-related fields."""
        for record in self:
            manager = record.manager_id
            record.manager_email = manager.email or False
            record.business_tech = manager.business_tech or False
            record.current_meeting_frequency = manager.current_meeting_frequency or False

    # @api.depends('gar')
    # def _compute_gar_banner(self):
    #     """Set banner text and color based on GAR value."""
    #     for record in self:
    #         if record.gar == 'green':
    #             record.gar_banner_text = 'GAR: GREEN - Everything is on track!'
    #             record.gar_banner_color = 'success'
    #         elif record.gar == 'amber':
    #             record.gar_banner_text = 'GAR: AMBER - Attention needed!'
    #             record.gar_banner_color = 'warning'
    #         elif record.gar == 'red':
    #             record.gar_banner_text = 'GAR: RED - Critical issues detected!'
    #             record.gar_banner_color = 'danger'
    #         else:
    #             record.gar_banner_text = False
    #             record.gar_banner_color = False
