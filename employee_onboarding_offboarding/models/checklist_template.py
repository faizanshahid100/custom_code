from email.policy import default

from odoo import models, fields, api

class ChecklistTemplate(models.Model):
    _name = "checklist.template"
    _description = "Checklist Template"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char("Template Name", required=True, tracking=True)
    description = fields.Text("Description")
    type = fields.Selection([
        ('onboarding', 'Onboarding'),
        ('offboarding', 'Offboarding')
    ], string="Checklist Type", required=True, default='onboarding', tracking=True)
    active = fields.Boolean("Active", default=True)

    line_ids = fields.One2many('checklist.template.line', 'template_id', string="Checklist Items")


class ChecklistTemplateLine(models.Model):
    _name = "checklist.template.line"
    _description = "Checklist Template Line"

    template_id = fields.Many2one('checklist.template', string="Template", ondelete="cascade")
    requirement = fields.Char("Requirement", required=True)
    responsible_user_id = fields.Many2one('res.users', string="Responsible Person", required=True)
    due_days = fields.Integer("Due Days", help="Number of days after employee joining/leaving to complete this task")
    notes = fields.Text("Notes")

