from odoo import models, fields, api
from dateutil import parser
import io
import base64
import xlsxwriter

class SurveyUserInput(models.Model):
    _inherit = 'survey.user_input'

    employee_id = fields.Many2one('hr.employee', string='Employee')
    client_id = fields.Many2one('res.partner','Client', related='employee_id.contractor')
    job_id = fields.Many2one('hr.job','Job', related='employee_id.job_id')
    response_date = fields.Date('Client Response Date', compute='_compute_response_date', store=True)

    @api.depends('employee_id', 'user_input_line_ids.question_id', 'user_input_line_ids.display_name')
    def _compute_response_date(self):
        for rec in self:
            # Filter for the line where question is "Date"
            date_line = rec.user_input_line_ids.filtered(lambda l: l.answer_type == 'date')
            if date_line:
                try:
                    # Try to parse the display_name as a date
                    parsed_date = parser.parse(date_line[0].display_name)
                    rec.response_date = parsed_date.date()
                except Exception:
                    rec.response_date = False
            else:
                rec.response_date = False

    from odoo import models, fields
    import io
    import base64
    import xlsxwriter

    class SurveyUserInput(models.Model):
        _inherit = 'survey.user_input'

        def action_export_survey_excel(self):
            # Get all completed survey participations
            records = self.search([('state', '=', 'done')])
            if not records:
                return False

            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            worksheet = workbook.add_worksheet('Completed Surveys')

            # Formats
            header_fmt = workbook.add_format({'bold': True, 'border': 1, 'align': 'center'})
            cell_fmt = workbook.add_format({'border': 1})
            number_fmt = workbook.add_format({'border': 1, 'align': 'center', 'num_format': '0.00'})

            # Column headers
            headers = ['Survey Name', 'Employee / Resource Name', "Manager's Name", 'Average Score']
            for col, h in enumerate(headers):
                worksheet.write(0, col, h, header_fmt)

            row = 1
            for rec in records:
                employee_name = ''
                manager_name = ''
                scores = []

                # Loop through each survey answer line
                for line in rec.user_input_line_ids:
                    q_title = (line.question_id.title or '').lower()

                    # Employee / Resource
                    if q_title in ['employee name', 'resource name']:
                        employee_name = (
                                line.value_char_box
                                or line.value_text
                                or (line.suggested_answer_id.value if line.suggested_answer_id else '')
                                or ''
                        )

                    # Manager
                    if q_title in ['manager name', "manager's name"]:
                        manager_name = (
                                line.value_char_box
                                or line.value_text
                                or (line.suggested_answer_id.value if line.suggested_answer_id else '')
                                or ''
                        )

                    # Score calculation
                    if line.answer_type == 'suggestion' and line.suggested_answer_id and line.suggested_answer_id.value:
                        val = line.suggested_answer_id.value.strip()
                        try:
                            # Only convert if it is a number
                            numeric_val = float(val)  # handles "1", "2.5", "0", etc.
                            scores.append(numeric_val)
                        except (ValueError, TypeError):
                            # Skip non-numeric values like "NO", "N/A", etc.
                            pass
                    # elif line.answer_type == 'numerical_box':
                    #     scores.append(float(line.display_name))
                    else:
                        pass

                # Calculate average score
                avg_score = round(sum(scores) / len(scores), 2) if scores else 0.0

                # Write data to Excel
                worksheet.write(row, 0, rec.survey_id.title or '', cell_fmt)
                worksheet.write(row, 1, employee_name, cell_fmt)
                worksheet.write(row, 2, manager_name, cell_fmt)
                worksheet.write(row, 3, avg_score, number_fmt)

                row += 1

            # Adjust column widths
            worksheet.set_column(0, 0, 30)
            worksheet.set_column(1, 2, 25)
            worksheet.set_column(3, 3, 15)

            workbook.close()
            output.seek(0)

            # Create attachment
            attachment = self.env['ir.attachment'].create({
                'name': 'Completed_Surveys_Report.xlsx',
                'type': 'binary',
                'datas': base64.b64encode(output.read()),
                'res_model': 'survey.user_input',
                'res_id': 0,  # generic export, not linked to a single record
                'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            })

            # Return download URL
            return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content/{attachment.id}?download=true',
                'target': 'self',
            }

