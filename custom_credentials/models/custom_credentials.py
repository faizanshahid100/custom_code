from odoo import api, fields, models, _
from odoo.exceptions import AccessError


class VPNConfig(models.Model):
    _name = "vpn.config"
    _inherit = "mail.thread"
    _description = "Environment/VPN"

    name = fields.Char()

class AccessTypeConfig(models.Model):
    _name = "access.type.config"
    _inherit = "mail.thread"
    _description = "Access types"

    name = fields.Char(string='Name')


class OfficeProject(models.Model):
    _name = "custom.credentials"
    _inherit = "mail.thread"
    _description = "Office Project Records"

    name = fields.Char(string='Name')
    project_id = fields.Many2one('project.project', string='Project', )
    vpn = fields.Char(string='Environment/VPN')
    access = fields.Selection([('application', 'Application'), ('machine', 'Machine'), ('db', 'DB'),('vpn', 'VPN'),
                               ('ftp', 'FTP')], string='Access type')
    access_configure = fields.Many2one('access.type.config', string='Access Types')
    vpn_configure = fields.Many2one('vpn.config', string='Environment/Vpn')

    my_url = fields.Char(string='URL/IP')
    user_name = fields.Char(string='User Name', required=True, )
    new_assignee_ids = fields.Many2many('res.users', string='Assignees',

                                        )
    # domain = "[('new_assignee_ids', 'in', [user.id])]"
    pswd = fields.Char(string='Password')
    schema = fields.Char(string='Schema')
    token = fields.Char(string='Token')
    internal_ip = fields.Char(string='Internal IP')

    additional_fields1  = fields.Char()
    additional_fields2  = fields.Char()
    additional_fields3  = fields.Char()
    additional_fields4  = fields.Char()
    additional_fields5  = fields.Char()
    notes = fields.Text(string='Notes')

    @api.model
    def create(self, vals):
        if not self.env.user.has_group('base.group_erp_manager'):
            # and self.env.user not in self.new_assignee_ids
            raise AccessError("You do not have permission to create this record.")
        # if 'new_assignee_ids' in vals:
        #     if self.env.user not in vals['new_assignee_ids'][0][2]:
        #         raise AccessError("You do not have permission to create this record.")
        return super(OfficeProject, self).create(vals)

    def write(self, vals):
        if not self.env.user.has_group('base.group_erp_manager'):
            # and self.env.user not in self.new_assignee_ids
            raise AccessError("You do not have permission to modify this record.")
        # if 'new_assignee_ids' in vals:
        #     if self.env.user not in vals['new_assignee_ids'][0][2]:
        #         raise AccessError("You do not have permission to modify this record.")
        return super(OfficeProject, self).write(vals)

    def unlink(self):
        # Check if the current user is in the new_assignee_ids field
        # for record in self:
        #     if self.env.user not in record.new_assignee_ids:
        if not self.env.user.has_group('base.group_erp_manager'):
            raise AccessError("You do not have permission to delete this record.")
        return super(OfficeProject, self).unlink()


