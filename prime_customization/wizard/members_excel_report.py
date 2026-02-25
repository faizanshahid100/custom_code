from odoo import models
import xlsxwriter
import base64
from io import BytesIO


class MembersExcelReport(models.TransientModel):
    _name = 'members.excel.report'
    _description = 'Members Excel Report'

    def generate_excel_report(self):
        partner_ids = self.env.context.get('active_ids', [])
        partners = self.env['res.partner'].browse(partner_ids)
        
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Members Report')
        
        header_format = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'border': 1})
        parent_format = workbook.add_format({'bold': True, 'font_size': 14, 'bg_color': '#4472C4', 'font_color': 'white'})
        cell_format = workbook.add_format({'border': 1})
        
        worksheet.set_column('A:A', 30)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 35)
        
        row = 0
        grouped_data = {}
        
        for partner in partners:
            if partner.child_ids:
                parent_name = partner.name
                if parent_name not in grouped_data:
                    grouped_data[parent_name] = []
                for child in partner.child_ids:
                    grouped_data[parent_name].append(child)
        
        if not grouped_data:
            for partner in partners:
                if partner.parent_id:
                    parent_name = partner.parent_id.name
                    if parent_name not in grouped_data:
                        grouped_data[parent_name] = []
                    grouped_data[parent_name].append(partner)
        
        for parent_name, members in grouped_data.items():
            worksheet.merge_range(row, 0, row, 2, f'{parent_name} Members', parent_format)
            row += 1
            
            worksheet.write(row, 0, 'Name', header_format)
            worksheet.write(row, 1, 'Designation', header_format)
            worksheet.write(row, 2, 'Email', header_format)
            row += 1
            
            for member in members:
                worksheet.write(row, 0, member.name or '', cell_format)
                worksheet.write(row, 1, dict(member._fields['designation'].selection).get(member.designation, '') if member.designation else '', cell_format)
                worksheet.write(row, 2, member.email or '', cell_format)
                row += 1
            
            row += 1
        
        workbook.close()
        output.seek(0)
        
        attachment = self.env['ir.attachment'].create({
            'name': 'Members_Report.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(output.read()),
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }
