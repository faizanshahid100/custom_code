from odoo import models, fields, api
from odoo.exceptions import ValidationError


class AssetManagementAssignment(models.Model):
    _name = 'asset.management.assignment'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = 'Asset Assignment'

    name = fields.Char(string='Assignment No', required=True, copy=False, readonly=True, default='New')
    date = fields.Date(string="Assignment Date", required=True, default=fields.Date.today, tracking=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, tracking=True)
    assignee_employee_id = fields.Many2one('hr.employee', string="Assignee", readonly=True, default=lambda self: self._default_assignee_employee())
    location_id = fields.Many2one('asset.management.location', string="Location", required=True, tracking=True)
    condition = fields.Integer(string="Condition (1-10)", related='asset_line_ids.asset_id.condition_rating', readonly=True, tracking=True)
    # 🔹 State field
    state = fields.Selection([
        ('in_store', 'In Store'),
        ('in_running', 'In Running'),
        ('in_repair', 'In Repair'),
        ('scraped', 'Scraped'),
    ], string="Status", default='in_store', tracking=True)
    asset_line_ids = fields.One2many('asset.management.assignment.line', 'assignment_id', string="Assigned Assets")

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('asset.assignment') or 'New'
        return super(AssetManagementAssignment, self).create(vals)

    # Default Assignee = logged-in user's employee record
    @api.model
    def _default_assignee_employee(self):
        employee = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
        return employee.id if employee else False

    # -------------------------------------
    # 🔹 State change actions with validation
    # -------------------------------------
    def _validate_state_change(self):
        """Prevent skipping 'in_store' when asset already allotted."""
        for rec in self.asset_line_ids:
            allotted_assets = rec.asset_id.is_allotted
            if allotted_assets and rec.state == 'in_store':
                raise ValidationError(
                    f"Assets {rec.asset_id.name} {rec.asset_id.serial_no} already allotted. Please set state to 'In Store' first before changing it to another state."
                )

    # -----------------------------
    # 🔹 State change button actions
    # -----------------------------
    def _update_asset_allocation(self):
        """Update the asset's is_allotted field based on assignment state."""
        for rec in self:
            is_allotted = rec.state != 'in_store'
            rec.asset_line_ids.mapped('asset_id').write({'is_allotted': is_allotted})

    def update_assets_allotment(self):
        for rec in self.asset_line_ids:
            if self.state == 'in_store':
                rec.asset_id.write({'is_allotted': True})
            elif self.state != 'in_store':
                rec.asset_id.write({'is_allotted': False})

    def action_set_in_store(self):
        self.update_assets_allotment()
        self.state = 'in_store'
        self._update_asset_allocation()

    def action_set_in_running(self):
        self.update_assets_allotment()
        self.state = 'in_running'
        self._update_asset_allocation()

    def action_set_in_repair(self):
        self.state = 'in_repair'
        self._update_asset_allocation()

    def action_set_scraped(self):
        self.state = 'scraped'
        self._update_asset_allocation()


class AssetManagementAssignmentLine(models.Model):
    _name = 'asset.management.assignment.line'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = 'Assigned Asset Line'

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
    @api.onchange('asset_id')
    def _onchange_asset_id(self):
        for rec in self:
            # if old asset existed → make it unallotted
            if rec._origin and rec._origin.asset_id and rec._origin.asset_id != rec.asset_id:
                rec._origin.asset_id.is_allotted = False
            # if new asset selected → mark allotted
            if rec.asset_id:
                rec.asset_id.is_allotted = True

    # -----------------------------------------
    # 🔹 Ensure data consistency at DB level
    # -----------------------------------------
    def write(self, vals):
        for rec in self:
            # If asset is being changed, unallot old one
            if 'asset_id' in vals and rec.asset_id:
                rec.asset_id.write({'is_allotted': False})
        res = super().write(vals)
        # Mark new asset as allotted
        if 'asset_id' in vals:
            self.mapped('asset_id').write({'is_allotted': True})
        return res

    def unlink(self):
        """When line deleted, unmark the asset."""
        self.mapped('asset_id').write({'is_allotted': False})
        return super().unlink()