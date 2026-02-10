import base64
import xml.etree.ElementTree as ET
from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import html


class ImportConnectwiseXMLWizard(models.TransientModel):
    _name = 'import.connectwise.xml.wizard'
    _description = 'Import ConnectWise XML'

    xml_file = fields.Binary(string='XML File', required=True)
    employee_id = fields.Many2one('hr.employee', default=lambda self: self._default_employee(), string='Employee')
    filename = fields.Char(string='File Name')

    @api.model
    def _default_employee(self):
        return self.env['hr.employee'].search(
            [('user_id', '=', self.env.uid)],
            limit=1
        )

    # ---------------------------------------------------------
    # Helper: Strip XML namespace
    # ---------------------------------------------------------
    def _tag(self, element):
        return element.tag.split('}', 1)[-1]

    def _clean_text(self, text):
        return html.unescape(text or '')

    def action_import(self):
        xml_data = base64.b64decode(self.xml_file)
        root = ET.fromstring(xml_data)

        employee = self.employee_id
        if not employee:
            raise UserError('Logged-in user has no linked employee.')

        # ---------------------------------------------------------
        # FIND table1_Group1_Collection (namespace-safe)
        # ---------------------------------------------------------
        group_collection = None
        for elem in root.iter():
            if self._tag(elem) == 'table1_Group1_Collection':
                group_collection = elem
                break

        if not group_collection:
            raise UserError(
                'Invalid ConnectWise XML: table1_Group1_Collection not found.'
            )

        # ---------------------------------------------------------
        # LOOP DAYS
        # ---------------------------------------------------------
        for day_node in group_collection:
            if self._tag(day_node) != 'table1_Group1':
                continue

            date_str = day_node.get('textbox29')
            total_hours = float(day_node.get('textbox54', 0.0))

            if not date_str:
                continue

            # "Mon, 01/26/2026" → 2026-01-26
            work_date = datetime.strptime(
                date_str.split(', ')[1], '%m/%d/%Y'
            ).date()

            timesheet = self.env['connectwise.timesheet'].create({
                'employee_id': employee.id,
                'work_date': work_date,
                'total_hours': total_hours,
            })

            # ---------------------------------------------------------
            # LOOP Group2
            # ---------------------------------------------------------
            for elem in day_node.iter():
                if self._tag(elem) != 'Detail':
                    continue

                self.env['connectwise.timesheet.line'].create({
                    'ticket': elem.get('textbox89'),
                    'internal_ticket': elem.get('textbox59'),
                    'timesheet_id': timesheet.id,
                    'timespan': elem.get('textbox80'),
                    'charge_to': elem.get('textbox82'),
                    'work_role': elem.get('textbox83'),
                    'actual_hours': float(elem.get('textbox86', 0.0)),
                    'is_ticket_closed': (elem.get('textbox85') or '').strip().lower() == 'yes',
                    'notes': self._clean_text(elem.get('textbox99')),
                })

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }