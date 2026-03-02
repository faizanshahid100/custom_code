from odoo import models, fields


class CeoProjectRole(models.Model):
    _name = 'ceo.project.role'
    _description = 'CEO Meeting - Project Role'

    name = fields.Char(string='Project Role', required=True)
    active = fields.Boolean(default=True)


class CeoScopeOfWork(models.Model):
    _name = 'ceo.scope.work'
    _description = 'CEO Meeting - Scope of Work'

    name = fields.Char(string='Scope of Work', required=True)
    active = fields.Boolean(default=True)


class CeoKpiDeliverable(models.Model):
    _name = 'ceo.kpi.deliverable'
    _description = 'CEO Meeting - KPI Deliverable'

    name = fields.Char(string='KPI Deliverable', required=True)
    active = fields.Boolean(default=True)


class CeoKadence(models.Model):
    _name = 'ceo.kadence'
    _description = 'CEO Meeting - Kadence'

    name = fields.Char(string='Kadence', required=True)
    active = fields.Boolean(default=True)
