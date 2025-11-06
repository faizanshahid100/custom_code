from odoo import models, fields, api
from odoo.exceptions import ValidationError


class AssetManagementAssignment(models.Model):
    _name = 'asset.management.assignment'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = 'Asset Assignment'

    name = fields.Char(string='Assignment No', required=True, copy=False, readonly=True, default='New')
    date = fields.Date(string="Assignment Date", required=True, default=fields.Date.today, tracking=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, tracking=True)
    assignee_user_id = fields.Many2one('res.users', string="Assignee", readonly=True)
    location_id = fields.Many2one('asset.management.location', string="Location", required=True, tracking=True)
    condition = fields.Integer(string="Condition (1-10)", related='asset_line_ids.asset_id.condition_rating', readonly=True, tracking=True)
    # 🔹 State field
    state = fields.Selection([
        ('in_store', 'In Store'),
        ('in_running', 'In Running'),
    ], string="Status", default='in_store', tracking=True)
    asset_line_ids = fields.One2many('asset.management.assignment.line', 'assignment_id', string="Assigned Assets")

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('asset.assignment') or 'New'
        return super(AssetManagementAssignment, self).create(vals)

    def _validate_duplicate_assets(self):
        """Raise error if same asset appears multiple times."""
        for rec in self:
            asset_ids = rec.asset_line_ids.mapped('asset_id.id')
            if len(rec.asset_line_ids) != len(set(asset_ids)):
                raise ValidationError(
                    "Duplicate assets detected in assignment lines. Each asset can only be assigned once.")

    # -------------------------------------
    # 🔹 State change actions with validation
    # -------------------------------------
    def _is_already_allotted(self):
        """Prevent skipping 'in_store' when asset already allotted."""
        for rec in self.asset_line_ids:
            if rec.asset_id.is_allotted:
                raise ValidationError(
                    f"Assets {rec.asset_id.name} {rec.asset_id.serial_no} already allotted. Please set state to 'In Store' first before changing it to another state."
                )

    def update_assets_allotment(self):
        for rec in self.asset_line_ids:
            if self.state == 'in_store':
                rec.asset_id.write({'is_allotted': True, 'assigned_id':self.id, 'state':'in_running'})
            elif self.state != 'in_store':
                rec.asset_id.write({'is_allotted': False, 'assigned_id':False, 'state': 'in_store'})
    # -----------------------------
    # 🔹 State change button actions
    # -----------------------------
    # def _update_asset_allocation(self):
    #     """Update the asset's is_allotted field based on assignment state."""
    #     for rec in self:
    #         is_allotted = rec.state != 'in_store'
    #         if rec.state != 'in_store':
    #             rec.asset_line_ids.mapped('asset_id').write({'is_allotted': is_allotted, 'assigned_id':self.id})
    #         elif rec.state == 'in_store':
    #             rec.asset_line_ids.mapped('asset_id').write({'is_allotted': False, 'assigned_id': False})


    def action_set_in_store(self):
        self.update_assets_allotment()
        self.write({'state': 'in_store', 'assignee_user_id': False})

    def action_set_in_running(self):
        self._validate_duplicate_assets()
        self._is_already_allotted()
        self.update_assets_allotment()
        self.write({'state': 'in_running', 'assignee_user_id': self.env.user.id})


class AssetManagementAssignmentLine(models.Model):
    _name = 'asset.management.assignment.line'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = 'Assigned Asset Line'

    category_id = fields.Many2one(
        'asset.management.category',
        string="Category",
        tracking=True,
        ondelete='set null'
    )

    asset_category_id = fields.Many2one('asset.management.category', string='Category')
    assignment_id = fields.Many2one('asset.management.assignment', string="Assignment", required=True, ondelete="cascade")
    asset_id = fields.Many2one('asset.management.asset', string="Asset", required=True, tracking=True)
    serial_no = fields.Char(string="Serial Name", related='asset_id.serial_no', store=True)
    model_name = fields.Char(string="Model Name", related='asset_id.model_name', store=True)
    processor = fields.Char(string="Processor Name", related='asset_id.processor', store=True)
    ram = fields.Char(string="Ram(GB)", related='asset_id.ram', store=True)
    storage = fields.Char(string="Storage(GB)", related='asset_id.storage', store=True)
    condition_rating = fields.Integer(string="Equipment Condition", related='asset_id.condition_rating', store=True)

    # -----------------------------------------
    # 🔹 Onchange - toggle is_allotted on select/unselect
    # -----------------------------------------
    # @api.onchange('asset_id')
    # def _onchange_asset_id(self):
    #     for rec in self:
    #         # if old asset existed → make it unallotted
    #         if rec._origin and rec._origin.asset_id and rec._origin.asset_id != rec.asset_id:
    #             rec._origin.asset_id.is_allotted = False
    #         # if new asset selected → mark allotted
    #         if rec.asset_id:
    #             rec.asset_id.is_allotted = True

    # -----------------------------------------
    # 🔹 Ensure data consistency at DB level
    # -----------------------------------------
    # def write(self, vals):
    #     for rec in self:
    #         # If asset is being changed, unallot old one
    #         if 'asset_id' in vals and rec.asset_id:
    #             rec.asset_id.write({'is_allotted': False})
    #     res = super().write(vals)
    #     # Mark new asset as allotted
    #     if 'asset_id' in vals:
    #         self.mapped('asset_id').write({'is_allotted': True})
    #     return res

    def unlink(self):
        """When line deleted, unmark the asset."""
        self.mapped('asset_id').write({'is_allotted': False})
        return super().unlink()