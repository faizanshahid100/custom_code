from odoo import models, fields

class AssetManagementCategory(models.Model):
    _name = 'asset.management.category'
    _description = 'IT Asset Category'
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Category Name", required=True, tracking=True)
    code = fields.Char(string="Category Code", tracking=True)
    description = fields.Text(string="Description")
