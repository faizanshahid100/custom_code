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
    hr_responsible = fields.Many2one('hr.employee', string='Hr Responsible')

    line_ids = fields.One2many('checklist.template.line', 'template_id', string="Checklist Items")
    post_line_ids = fields.One2many('post.checklist.template.line', 'template_id', string="Checklist Items")


class ChecklistTemplateLine(models.Model):
    _name = "checklist.template.line"
    _description = "Checklist Template Line"

    template_id = fields.Many2one('checklist.template', string="Template", ondelete="cascade")
    requirement = fields.Char("Requirement", required=True)
    responsible_user_id = fields.Many2one('res.users', string="Responsible Person", required=True)
    task_type = fields.Selection([("before", "Before"), ("after", "After")], string=" ", required=True, default="before" )
    due_days = fields.Integer("Joining Days", help="Number of days before employee joining to complete this task")
    notes = fields.Text("Notes")


class PostCheckListTemplate(models.Model):
    _name = "post.checklist.template.line"
    _description = "Post Onboarding Checklist"

    template_id = fields.Many2one('checklist.template', string="Template", ondelete="cascade")
    requirement = fields.Char("Requirement", required=True)
    responsible_user_id = fields.Many2one('res.users', string="Responsible Person", required=True)
    post_days = fields.Integer("After Joining Days", help="Number of days after employee joining to complete this task")
    notes = fields.Text("Notes")