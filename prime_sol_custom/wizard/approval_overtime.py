# -*- coding: utf-8 -*-
from odoo import models, fields
from datetime import datetime
import io
import base64
import xlsxwriter

class ApprovalOvertime(models.TransientModel):
    _name = 'approval.overtime'
    _description = 'Overtime Approval Wizard'

    def _default_start_date(self):
        """Return the first day of the current month at 00:00:00"""
        now = datetime.now()
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    def _default_end_date(self):
        """Return current datetime"""
        return datetime.now()

    start_date = fields.Datetime(
        string='Start Date',
        required=True,
        default=_default_start_date
    )
    end_date = fields.Datetime(
        string='End Date',
        required=True,
        default=_default_end_date
    )
    request_owner_ids = fields.Many2many(
        'res.users',
        string='Request Owners'
    )

    # For Excel Report
    my_xl_file = fields.Binary('Excel Report')
    file_name = fields.Char('File Name')

    # Action method
    def action_submit_overtime(self):
        # --- 1. Build domain for search ---
        domain = [
            ('request_status', '=', 'approved'),
            ('category_id.name', '=', 'Overtime'),
            ('date_start', '>=', self.start_date),
            ('date_start', '<=', self.end_date),
        ]
        if self.request_owner_ids:
            domain.append(('request_owner_id', 'in', self.request_owner_ids.ids))

        overtime_recs = self.env['approval.request'].sudo().search(domain)

        # --- 2. Create Excel ---
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Overtime Report')

        # Styles
        header = workbook.add_format({'bold': True, 'bg_color': '#A7C7E7', 'border': 1})
        normal = workbook.add_format({'border': 1})

        # Set column widths
        sheet.set_column('A:A', 20)  # Request ID
        sheet.set_column('B:B', 30)  # Request Owner
        sheet.set_column('C:C', 15)  # Category
        sheet.set_column('D:E', 20)  # Start Date, End Date
        sheet.set_column('F:G', 10)  # Hours, Status

        # Headers
        columns = ['Request ID', 'Request Owner', 'Category', 'Start Date', 'End Date', 'Hours', 'Status']
        for col, name in enumerate(columns):
            sheet.write(0, col, name, header)

        # Data rows
        row = 1
        for rec in overtime_recs:
            sheet.write(row, 0, rec.name or '', normal)
            sheet.write(row, 1, rec.request_owner_id.name or '', normal)
            sheet.write(row, 2, rec.category_id.name or '', normal)
            sheet.write(row, 3, rec.date_start.strftime('%d-%b-%Y %H:%M') if rec.date_start else '', normal)
            sheet.write(row, 4, rec.date_end.strftime('%d-%b-%Y %H:%M') if rec.date_end else '', normal)
            sheet.write(row, 5, f"{int((rec.date_end - rec.date_start).total_seconds()//3600)}h:{int(((rec.date_end - rec.date_start).total_seconds()%3600)//60):02d}m" if rec.date_start and rec.date_end else '', normal)
            # sheet.write(row, 5, (rec.date_end - rec.date_start).strftime('%H:%M'), normal)
            sheet.write(row, 6, rec.request_status or '', normal)
            row += 1

        workbook.close()
        output.seek(0)
        file_data = output.read()
        output.close()

        # --- 3. Save file in wizard and trigger download ---
        file_name = f"Overtime_Report_{self.start_date.strftime('%d%b%Y')}_to_{self.end_date.strftime('%d%b%Y')}.xlsx"
        self.write({
            'my_xl_file': base64.b64encode(file_data),
            'file_name': file_name
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/?model={self._name}&id={self.id}&field=my_xl_file&download=true&filename={file_name}',
            'target': 'self',
        }
