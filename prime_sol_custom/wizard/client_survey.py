from datetime import date, timedelta
from odoo import api, fields, models
from odoo.exceptions import ValidationError
import io
import xlsxwriter
import base64
from io import BytesIO
import xlwt

class ClientSurvey(models.TransientModel):
    _name = "client.survey"
    _description = 'Client Survey'

    @api.model
    def default_get(self, default_fields):
        res = super(ClientSurvey, self).default_get(default_fields)
        today = date.today()

        # ✅ First day of the current year
        first_day_current_year = date(today.year, 1, 1)

        res.update({
            'date_from': first_day_current_year or False,
            'date_to': today or False,
            'partner_id': self.env.user.employee_id.contractor.id if self.env.user.employee_id.contractor else False,
            'department_id': self.env.user.employee_id.department_id.id if self.env.user.employee_id.department_id else False,
        })
        return res

    date_from = fields.Date(string="Start Date", required=True)
    date_to = fields.Date(string="End Date", required=True)
    partner_id = fields.Many2one('res.partner', string="Company", domain=[('is_company', '=', True)])
    department_id = fields.Many2one('hr.department', string='Department')

    # For Excel Report
    my_xl_file = fields.Binary('Excel Report')
    file_name = fields.Char('File Name')

    def action_confirm(self):
        workbook = xlwt.Workbook(encoding='utf-8')
        worksheet = workbook.add_sheet('Department wise Head Count', cell_overwrite_ok=True)

        table_heading_style = xlwt.easyxf(
            'font: bold on,height 220;align: wrap on,vert centre, horiz center; align: wrap yes,vert centre, horiz center;pattern: pattern solid, fore-colour aqua;border: left thin,right thin,top thin,bottom thin')
        columns_left_bold_style = xlwt.easyxf(
            'font: height 200;align: wrap on,vert centre, horiz left; align: wrap yes,vert centre; border: left thin,right thin,top thin,bottom thin')

        worksheet.col(0).width = 5000
        worksheet.col(1).width = 7000
        worksheet.col(2).width = 4000
        worksheet.col(3).width = 7000
        worksheet.col(4).width = 4000
        worksheet.col(5).width = 5000

        for wizard in self:
            pass

        worksheet.write(0, 0, 'Response Date', table_heading_style)
        worksheet.write(0, 1, 'Employee', table_heading_style)
        worksheet.write(0, 2, 'Client', table_heading_style)
        worksheet.write(0, 3, 'Manager (Client)', table_heading_style)
        worksheet.write(0, 4, 'Level', table_heading_style)
        worksheet.write(0, 5, 'Avg. Points', table_heading_style)
        # Get survey responses
        if self.partner_id:
            inputs = self.env['survey.user_input'].search([('response_date', '>=', self.date_from), ('response_date', '<=', self.date_to),('employee_id', '!=', False), ('state', '=', 'done'), ('survey_id.title', '=', '2025: Employee Performance Feedback'), ('test_entry', '=', False), ('partner_id', '=', self.partner_id.id)])
        elif not self.partner_id:
            inputs = self.env['survey.user_input'].search([('response_date', '>=', self.date_from), ('response_date', '<=', self.date_to),('employee_id', '!=', False), ('state', '=', 'done'), ('survey_id.title', '=', '2025: Employee Performance Feedback'), ('test_entry', '=', False),])

        if not inputs:
            raise ValidationError('There is no survey regarding the parameters')

        row = 1
        for input in inputs:
            suggested_values = [
                float(val) for val in input.user_input_line_ids
                .filtered(lambda l: l.answer_type == 'suggestion')
                .mapped('suggested_answer_id.value') if val.replace('.', '', 1).isdigit()
            ]
            average = sum(suggested_values) / len(suggested_values) if suggested_values else 0
            worksheet.write(row, 0, input.response_date.strftime('%d-%m-%Y') if input.response_date else '', columns_left_bold_style)
            worksheet.write(row, 1, input.employee_id.name or '', columns_left_bold_style)
            worksheet.write(row, 2, input.partner_id.name or '', columns_left_bold_style)
            worksheet.write(row, 3, input.employee_id.manager or '', columns_left_bold_style)
            worksheet.write(row, 4, input.employee_id.level or '', columns_left_bold_style)
            worksheet.write(row, 5, f"{average:.2f}" if average else '', columns_left_bold_style)
            row += 1

        stream = BytesIO()
        workbook.save(stream)
        excel_file = base64.encodebytes(stream.getvalue())
        wizard.my_xl_file = excel_file
        wizard.file_name = 'client_survey_Report.xls'
        stream.close()

        return {
            'type': 'ir.actions.act_url',
            'url': 'web/content/?model=client.survey&field=my_xl_file&download=true&id=%s&filename=%s' % (
                self.id, 'client_survey_Report.xls'),
        }