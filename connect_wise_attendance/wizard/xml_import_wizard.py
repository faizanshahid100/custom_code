import base64
import xml.etree.ElementTree as ET
from odoo import models, fields, api
from odoo.exceptions import UserError
import logging
import re
from datetime import datetime

_logger = logging.getLogger(__name__)

class XmlImportWizard(models.TransientModel):
    _name = 'xml.import.wizard'
    _description = 'XML Import Wizard'

    xml_file = fields.Binary('XML File', required=True)
    filename = fields.Char('Filename')

    def import_xml(self):
        if not self.xml_file:
            raise UserError('Please select an XML file to import.')
        
        try:
            xml_data = base64.b64decode(self.xml_file)
            root = ET.fromstring(xml_data)
            records_created = 0
            
            # Extract employee and date from root attributes
            employee_id = self._extract_employee(root)
            date = self._extract_date(root)
            
            # Find elements that end with 'Detail' - these contain the actual time entry data
            for element in root.iter():
                if element.tag.endswith('Detail') and element.attrib:
                    vals = {
                        'name': f"Time Entry {records_created + 1}",
                        'employee_id': employee_id,
                        'date': date,
                        'notes': '\n'.join([f'{k}: {v}' for k, v in element.attrib.items()]),
                        'tag_active': True,
                    }
                    
                    self.env['connect.wise.attendance'].create(vals)
                    records_created += 1
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Import Result',
                    'message': f'{records_created} records imported successfully.',
                    'type': 'success' if records_created > 0 else 'warning',
                }
            }
            
        except ET.ParseError as e:
            raise UserError(f'Invalid XML file format: {e}')
        except Exception as e:
            raise UserError(f'Error importing XML: {str(e)}')
    
    def _extract_employee(self, root):
        # Extract member name from textbox5 attribute
        textbox5 = root.get('textbox5', '')
        match = re.search(r'Member:\s*([^\\n]+)', textbox5)
        if not match:
            return self._get_fallback_employee()
        
        member_name = match.group(1).strip()
        name_parts = member_name.split()
        
        if not name_parts:
            return self._get_fallback_employee()
        
        # Progressive name matching
        employees = self.env['hr.employee']
        for i in range(len(name_parts)):
            search_name = ' '.join(name_parts[:i+1])
            found_employees = self.env['hr.employee'].search([('name', 'ilike', search_name)])
            if len(found_employees) == 1:
                return found_employees.id
            elif len(found_employees) > 1:
                employees = found_employees
        
        # If multiple matches, try exact match
        if employees:
            exact_match = employees.filtered(lambda e: e.name.lower() == member_name.lower())
            if exact_match:
                return exact_match[0].id
            return employees[0].id
        
        return self._get_fallback_employee()
    
    def _extract_date(self, root):
        # Extract date from textbox7 attribute
        textbox7 = root.get('textbox7', '')
        date_match = re.search(r'(\d{2}/\d{2}/\d{4})', textbox7)
        if date_match:
            try:
                return datetime.strptime(date_match.group(1), '%m/%d/%Y').date()
            except ValueError:
                pass
        return fields.Date.today()
    
    def _get_fallback_employee(self):
        employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        return employee.id if employee else False
