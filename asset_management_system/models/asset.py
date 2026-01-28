from email.policy import default

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import base64
import io
import qrcode


class AssetManagementAsset(models.Model):
    _name = 'asset.management.asset'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = 'IT Product'

    name = fields.Char(string="Product Name", required=True, tracking=True)
    employee_name = fields.Char('Employee Name')
    asset_category_id = fields.Many2one('asset.management.category', string='Category', tracking=True)
    state = fields.Selection([
        ('in_store', 'In Store'),
        ('in_running', 'In Running'),
        ('in_repair', 'In Repair'),
        ('scraped', 'Scraped'),
    ], string="Status", default='in_store', tracking=True)
    sequence_no = fields.Char(string='Product No', required=True, copy=False, readonly=True, default='New', tracking=True)
    serial_no = fields.Char(string="Serial No.", required=True, tracking=True)
    qr_code = fields.Binary("QR Code", readonly=True)
    model_name = fields.Char(string="Model", required=True, tracking=True)
    processor = fields.Char(string="Processor", tracking=True)
    purchase_date = fields.Date('Purchase Date', default=lambda self: fields.Date.today(), tracking=True)
    purchase_price = fields.Float('Purchase Price', tracking=True)
    ram = fields.Char(string="RAM", tracking=True)
    storage = fields.Char(string="Storage", tracking=True)
    condition_rating = fields.Integer(string="Equipment Condition (1-10)", default=10, required=True, tracking=True)
    reason_below_8 = fields.Text(string="Reason (if below 8)", readonly=False, tracking=True)
    comments = fields.Text('Comments', tracking=True)
    is_allotted = fields.Boolean('Is Allotted', default=False, tracking=True)
    is_in_repair = fields.Boolean('In Repair', default=False, tracking=True)
    is_in_scrap = fields.Boolean('In Scrap', default=False, tracking=True)
    assigned_id = fields.Many2one('asset.management.assignment', string='Assigned To')
    asset_history_line_ids = fields.One2many('asset.history.line', 'asset_id', string="Product History")

    display_name = fields.Char()

    employee_id = fields.Many2one('hr.employee', string='Assigned To')

    # Generate QR Code
    def _generate_qr_code(self):
        """Generate QR code using serial_no, category name, and sequence_no"""
        for rec in self:
            if rec.serial_no and rec.asset_category_id and rec.sequence_no:
                qr_content = f"Serial No: {rec.serial_no}\nCategory: {rec.asset_category_id.name}\nProduct Seq: {rec.sequence_no}"
                qr_img = qrcode.make(qr_content)
                buffer = io.BytesIO()
                qr_img.save(buffer, format="PNG")
                rec.qr_code = base64.b64encode(buffer.getvalue())
    def name_get(self):
        result = []
        for rec in self:
            name = rec.name
            if rec.serial_no:
                name = f"{rec.name} {rec.model_name} ({rec.serial_no})"
            result.append((rec.id, name))
        return result

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
            category_id = vals.get('asset_category_id')
            if not category_id:
                raise ValidationError('Please select Product Category before creating Product.')

            category = self.env['asset.management.category'].browse(category_id)

            if not category.code:
                raise ValidationError('Product Category must have a Code.')

            sequence_code = f'asset.management.asset.{category.code}'

            seq = self.env['ir.sequence'].search(
                [('code', '=', sequence_code)],
                limit=1
            )

            if not seq:
                seq = self.env['ir.sequence'].create({
                    'name': f'Product Sequence {category.code}',
                    'code': sequence_code,
                    'prefix': f'{category.code}/',
                    'padding': 4,
                    'number_increment': 1,
                })

            vals['sequence_no'] = self.env['ir.sequence'].next_by_code(sequence_code)

        record = super(AssetManagementAsset, self).create(vals)
        record._generate_qr_code()
        return record

    def write(self, vals):
        if 'asset_category_id' in vals:
            for rec in self:
                if rec.asset_category_id and vals.get('asset_category_id') != rec.asset_category_id.id:
                    raise ValidationError(
                        'You cannot change the Product category after Product creation.'
                    )

        state_before = {rec.id: rec.state for rec in self}

        res = super().write(vals)
        if any(field in vals for field in ['serial_no', 'asset_category_id', 'sequence_no']):
            self._generate_qr_code()

        if 'state' in vals:
            for asset in self:
                old_state = state_before.get(asset.id)
                new_state = asset.state

                if old_state != new_state:
                    asset._create_history_line(new_state)

                # Clear employee when not running
                if new_state != 'in_running':
                    asset.employee_id = False

        return res

    def unlink(self):
        if not self.env.user.has_group('base.group_system'):
            raise ValidationError(
                'Only an Administrator is allowed to delete an Product.'
            )
        return super(AssetManagementAsset, self).unlink()

    def _create_history_line(self, state):
        vals = {
            'asset_id': self.id,
            'state': state,
            'assign_date': fields.Date.today(),
        }

        # Assign employee ONLY when running
        if state == 'in_running':
            if not self.employee_id:
                raise ValidationError(
                    'Employee must be assigned before moving Product to In Running.'
                )
            vals['employee_id'] = self.employee_id.id

        self.env['asset.history.line'].create(vals)

    def action_set_in_store(self):
        self.write({'state': 'in_store', 'is_allotted': False,'is_in_repair': False, 'is_in_scrap':False, 'employee_id':False, 'employee_name':False})
    def action_set_in_repair(self):
        if self.state == 'in_store':
            self.write({'state': 'in_repair', 'is_in_repair': True })
        else:
            raise ValidationError('Please move the Product to the Store first.')

    def action_set_scraped(self):
        if self.state == 'in_store':
            self.write({'state': 'scraped', 'is_in_scrap': True})
        else:
            raise ValidationError('Please move the Product to the Store first.')

    def action_set_in_running(self):
        if not self.employee_id:
            raise ValidationError('Please assign an employee before marking Product as In Running.')
        # if self.state != 'in_store':
        #     raise ValidationError('Product must be in Store before assigning.')
        self.write({
            'state': 'in_running',
            'employee_name': self.employee_id.name
        })


    @api.constrains('serial_no')
    def _check_serial_no_unique(self):
        for rec in self:
            if rec.serial_no:
                existing = self.search([('serial_no', '=', rec.serial_no), ('id', '!=', rec.id)])
                if existing:
                    raise ValidationError(f'Serial Number "{rec.serial_no}" must be unique!')

class AssetsHistory(models.Model):
    _name = 'asset.history.line'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = 'IT Product Usage History'
    _order = 'id desc'

    employee_id = fields.Many2one('hr.employee', string="Employee", tracking=True)
    assign_date = fields.Date('Assign Date')
    # return_date = fields.Date('Assign Date', default=lambda self: fields.Date.today())
    # assigned_by_id = fields.Many2one('res.users', 'Assign By')
    # return_by_id = fields.Many2one('res.users', 'Return By')
    # assignment_id = fields.Many2one('asset.management.assignment', string="Assignment", required=True,
    #                                 ondelete="cascade")
    asset_id = fields.Many2one('asset.management.asset', string="Product", required=True, tracking=True, ondelete='cascade')
    state = fields.Selection([
        ('in_store', 'In Store'),
        ('in_running', 'In Running'),
        ('in_repair', 'In Repair'),
        ('scraped', 'Scraped'),
    ], string="Status", default='in_store', tracking=True)