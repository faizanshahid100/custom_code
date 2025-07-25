from odoo import models, fields,api
from odoo.exceptions import ValidationError
from datetime import timedelta, datetime


class GazettedHoliday(models.Model):
    _name = 'gazetted.holiday'
    _description = 'Gazetted Holiday'

    name = fields.Char(string='Leave Policy', required=True)
    country_id = fields.Many2one('res.country', string='Country')
    holiday_dates = fields.Char(string='Holiday Dates', compute='_compute_dates', store=True)
    line_ids = fields.One2many('gazetted.holiday.line', 'holiday_id', string='Holiday Dates')

    @api.depends('line_ids.date_from', 'line_ids.date_to')
    def _compute_dates(self):
        for rec in self:
            all_dates = []
            for line in rec.line_ids:
                if line.date_from and line.date_to and line.date_from <= line.date_to:
                    current_day = line.date_from
                    while current_day <= line.date_to:
                        all_dates.append(current_day.strftime('%d-%m-%Y'))
                        current_day += timedelta(days=1)
            # Remove duplicates and sort
            unique_sorted = sorted(set(all_dates), key=lambda d: datetime.strptime(d, '%d-%m-%Y'))
            rec.holiday_dates = str(unique_sorted)


class GazettedHolidayLine(models.Model):
    _name = 'gazetted.holiday.line'
    _description = 'Gazetted Holiday Line'

    holiday_id = fields.Many2one('gazetted.holiday', string='Gazetted Holiday', ondelete='cascade', required=True)
    day = fields.Char('Day')
    description = fields.Char(string='Description')
    date_from = fields.Date(string='Date From', required=True)
    date_to = fields.Date(string='Date To', required=True)
    total_holidays = fields.Float('Total Holidays', compute='_compute_total_holidays')

    @api.constrains('date_from', 'date_to')
    def _check_date_range(self):
        for rec in self:
            if rec.date_from and rec.date_to and rec.date_to < rec.date_from:
                raise ValidationError("The 'Date To' cannot be earlier than 'Date From'.")

    @api.depends('date_from', 'date_to')
    def _compute_total_holidays(self):
        for rec in self:
            if rec.date_from and rec.date_to and rec.date_to >= rec.date_from:
                rec.total_holidays = (rec.date_to - rec.date_from).days + 1  # inclusive
            else:
                rec.total_holidays = 0