# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError, UserError
import io
import base64
from datetime import timedelta
import xlsxwriter

class HrPayslipRunExt(models.Model):
    _inherit = 'hr.payslip.run'

    conversion_rate = fields.Float(string='Conversion Rate $', digits=(12, 6))