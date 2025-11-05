from odoo import models, fields

class AssetManagementLocation(models.Model):
    _name = 'asset.management.location'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = 'Asset Location'

    name = fields.Char(string="Location Name", required=True, tracking=True)
    description =  fields.Text('Description', tracking=True)