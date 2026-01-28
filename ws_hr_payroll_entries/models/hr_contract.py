# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, date


class HrContract(models.Model):
    _inherit = 'hr.contract'

    payslip_currency_id = fields.Many2one('res.currency', string="Payslip Currency", readonly=False)
    travel_allowances = fields.Monetary('Travel Allowances', currency_field='payslip_currency_id', tracking=True)
    fuel_allowances = fields.Monetary('Fuel Allowances', currency_field='payslip_currency_id', tracking=True)
    relocation_allowances = fields.Monetary('Relocation Allowances', currency_field='payslip_currency_id', tracking=True)
    wage = fields.Monetary('Wage', currency_field='payslip_currency_id', required=True, tracking=True, help="Employee's monthly gross wage.")


    def read(self, fields=None, load='_classic_read'):
        self._log_contract_access()
        return super(HrContract, self).read(fields=fields, load=load)

    def _log_contract_access(self):
        user = self.env.user
        msg = f"🕵️ User <b>{user.name}</b> (Login: {user.login}) accessed <code>{self.name}'s</code> contract on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}."

        # 1. Log in channel
        channel = self.env.ref('ws_hr_payroll_entries.channel_contract_access', raise_if_not_found=False)
        if channel:
            channel.message_post(
                body=msg,
                message_type="comment",
                subtype_xmlid="mail.mt_note"
            )

        # 2. Send email
        if user.id != 2:
            mail_values = {
                'subject': "Contract Access Alert",
                'body_html': f"<p>{msg}</p>",
                'email_to': "adnan@primesystemsolutions.com",
                'email_from': "hr@primesystemsolutions.com",
            }
            self.env['mail.mail'].sudo().create(mail_values).send()

class HrContractHistory(models.Model):
    _inherit = 'hr.contract.history'

    def read(self, fields=None, load='_classic_read'):
        self._log_contract_history_access()
        return super(HrContractHistory, self).read(fields=fields, load=load)

    def _log_contract_history_access(self):
        user = self.env.user
        msg = f"🕵️ User <b>{user.name}</b> (Login: {user.login}) accessed <code>{self.name}'s</code> contract history on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}."

        # 1. Log in channel
        channel = self.env.ref('ws_hr_payroll_entries.channel_contract_access', raise_if_not_found=False)
        if channel:
            channel.message_post(
                body=msg,
                message_type="comment",
                subtype_xmlid="mail.mt_note"
            )

        # 2. Send email
        mail_values = {
            'subject': "Contract History Access Alert",
            'body_html': f"<p>{msg}</p>",
            'email_to': "adnan@primesystemsolutions.com",
            'email_from': "hr@primesystemsolutions.com",
        }
        self.env['mail.mail'].sudo().create(mail_values).send()