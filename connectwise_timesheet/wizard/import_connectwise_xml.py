import base64
import xml.etree.ElementTree as ET
from datetime import datetime

from odoo import models, fields
from odoo.exceptions import UserError


class ImportConnectwiseXMLWizard(models.TransientModel):
    _name = 'import.connectwise.xml.wizard'
    _description = 'Import ConnectWise XML'

    xml_file = fields.Binary(string='XML File', required=True)
    filename = fields.Char(string='File Name')

    # ---------------------------------------------------------
    # Helper: Strip XML namespace
    # ---------------------------------------------------------
    def _tag(self, element):
        return element.tag.split('}', 1)[-1]

    def action_import(self):
        xml_data = base64.b64decode(self.xml_file)
        root = ET.fromstring(xml_data)

        employee = self.env.user.employee_id
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
                    'timesheet_id': timesheet.id,
                    'timespan': elem.get('textbox80'),
                    'charge_to': elem.get('textbox82'),
                    'work_role': elem.get('textbox83'),
                    'actual_hours': float(elem.get('textbox86', 0.0)),
                    'notes': elem.get('textbox99'),
                })

        return {'type': 'ir.actions.act_window_close'}