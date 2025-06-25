# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class HolidaysType(models.Model):
    _inherit = "hr.leave.type"


    department_ids = fields.Many2many('hr.department', string='Department')
    employee_ids = fields.Many2many('hr.employee', string='Employees')

    #search method
    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        args = args + ['|',('employee_ids','=',False) ,self.get_domain()]
        return super(HolidaysType, self).search(args, offset=offset, limit=limit, order=order, count=count)

    #name search method
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        res = super(HolidaysType, self).name_search(name, args, operator, limit=limit)
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('number', '=', name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()

    #read group method
    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        domain = domain + ['|',('employee_ids','=',False) ,self.get_domain()]
        return super(HolidaysType, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)

    #set domain function
    def get_domain(self):
        employee = self.env.user.employee_id
        if employee:
            return ('employee_ids', 'in', [employee.id])
        return ('employee_ids', 'in', [])
