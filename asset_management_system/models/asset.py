from email.policy import default

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class AssetManagementAsset(models.Model):
    _name = 'asset.management.asset'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = 'IT Asset'
    _rec_name = 'display_name'

    name = fields.Char(string="Asset Name", required=True, tracking=True)
    state = fields.Selection([
        ('in_store', 'In Store'),
        ('in_running', 'In Running'),
        ('in_repair', 'In Repair'),
        ('scraped', 'Scraped'),
    ], string="Status", default='in_store', tracking=True)
    sequence_no = fields.Char(string='Asset No', required=True, copy=False, readonly=True, default='New', tracking=True)
    serial_no = fields.Char(string="Serial No.", required=True, tracking=True)
    model_name = fields.Char(string="Model", required=True, tracking=True)
    processor = fields.Char(string="Processor", tracking=True)
    ram = fields.Char(string="RAM", tracking=True)
    storage = fields.Char(string="Storage", tracking=True)
    condition_rating = fields.Integer(string="Equipment Condition (1-10)", default=10, required=True, tracking=True)
    reason_below_8 = fields.Text(string="Reason (if below 8)", readonly=False, tracking=True)
    is_allotted = fields.Boolean('Is Allotted', default=False, tracking=True)
    is_in_repair = fields.Boolean('In Repair', default=False, tracking=True)
    is_in_scrap = fields.Boolean('In Scrap', default=False, tracking=True)
    assigned_id = fields.Many2one('asset.management.assignment', string='Assigned To')

    display_name = fields.Char(compute='_compute_display_name', store=True)

    @api.depends('name', 'serial_no')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"{rec.name} ({rec.serial_no})" if rec.serial_no else rec.name

    @api.onchange('condition_rating')
    def _onchange_condition_rating(self):
        for rec in self:
            if rec.condition_rating < 8:
                rec.reason_below_8 = ''
            else:
                rec.reason_below_8 = False

    @api.model
    def create(self, vals):
        if vals.get('sequence_no', 'New') == 'New':
            vals['sequence_no'] = self.env['ir.sequence'].next_by_code('asset.management.asset') or 'New'
        return super(AssetManagementAsset, self).create(vals)

    def action_set_in_store(self):
        self.write({'state': 'in_store', 'is_allotted': False,'is_in_repair': False, 'is_in_scrap':False, 'assigned_id':False})
    def action_set_in_repair(self):
        if self.state == 'in_store':
            self.write({'state': 'in_repair', 'is_in_repair': True })
        else:
            raise ValidationError('Please move the asset to the Store first.')

    def action_set_scraped(self):
        if self.state == 'in_store':
            self.write({'state': 'scraped', 'is_in_scrap': True})
        else:
            raise ValidationError('Please move the asset to the Store first.')