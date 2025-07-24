from odoo import models, fields,api


class GazettedHoliday(models.Model):
    _name = 'gazetted.holiday'
    _description = 'Gazetted Holiday'

    name = fields.Char(string='Leave Policy', required=True)
    country_id = fields.Many2one('res.country', string='Country', required=True)
    year = fields.Char(string='Year', required=True)
    line_ids = fields.One2many('gazetted.holiday.line', 'holiday_id', string='Holiday Dates')


class GazettedHolidayLine(models.Model):
    _name = 'gazetted.holiday.line'
    _description = 'Gazetted Holiday Line'

    holiday_id = fields.Many2one('gazetted.holiday', string='Gazetted Holiday', ondelete='cascade', required=True)
    day = fields.Char('Day')
    date = fields.Date(string='Date', required=True)
    description = fields.Char(string='Description')
    day_name = fields.Char(string='Day Name', compute='_compute_day_info', store=True)

    @api.depends('date')
    def _compute_day_info(self):
        for rec in self:
            if rec.date:
                dt = fields.Date.from_string(rec.date)
                rec.day_name = dt.strftime('%A')
            else:
                rec.day_name = ''
