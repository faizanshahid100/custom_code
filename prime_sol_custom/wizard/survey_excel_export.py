# -*- coding: utf-8 -*-
import base64
import io
from odoo import models, fields, api
from odoo.exceptions import UserError

try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None


class SurveyExcelExport(models.TransientModel):
    _name = 'survey.excel.export'
    _description = 'Survey Excel Export'

    survey_id = fields.Many2one('survey.survey', string='Survey', required=True)
    excel_file = fields.Binary(string='Excel File', readonly=True)
    file_name = fields.Char(string='File Name', readonly=True)

    def action_export_excel(self):
        if not xlsxwriter:
            raise UserError("Please install xlsxwriter: pip install xlsxwriter")
        
        survey = self.survey_id
        if not survey.user_input_ids:
            raise UserError("No survey responses found to export.")

        # Create Excel file in memory
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Sheet1')

        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D7E4BC',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })
        
        cell_format = workbook.add_format({
            'border': 1,
            'align': 'left',
            'valign': 'top',
            'text_wrap': True
        })
        
        number_format = workbook.add_format({
            'border': 1,
            'align': 'center',
            'num_format': '0.00'
        })

        # Get all questions (excluding pages) in sequence order
        questions = survey.question_ids.filtered(lambda q: not q.is_page).sorted('sequence')
        
        # Prepare headers - start with basic info like the original template
        headers = ['Employee Name', "Manager's Name", 'Date']
        
        # Track matrix questions for average calculation
        matrix_questions = []
        matrix_column_indices = []
        
        # Add question headers
        for question in questions:
            if question.question_type == 'matrix':
                matrix_questions.append(question)
                # Add matrix sub-questions (rows) as separate columns
                for row in question.matrix_row_ids.sorted('sequence'):
                    header = f"{question.title} - {row.value}"
                    headers.append(header)
                    matrix_column_indices.append(len(headers) - 1)
            else:
                headers.append(question.title)
        
        # Add average column for matrix questions if any exist
        if matrix_questions:
            headers.append('Average Score')

        # Write headers
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)

        # Get completed responses
        responses = survey.user_input_ids.filtered(lambda r: r.state == 'done')
        
        # Write data rows
        row = 1
        for response in responses:
            col = 0
            
            # Basic info - Employee Name, Manager Name, Date
            worksheet.write(row, col, response.employee_id.name or '', cell_format)
            col += 1
            
            # Find manager name from survey responses (assuming it's in a question)
            manager_name = ''
            manager_question = questions.filtered(lambda q: 'manager' in q.title.lower())
            if manager_question:
                manager_answer = response.user_input_line_ids.filtered(lambda l: l.question_id == manager_question[0])
                if manager_answer:
                    manager_name = manager_answer[0].value_char_box or manager_answer[0].display_name or ''
            worksheet.write(row, col, manager_name, cell_format)
            col += 1
            
            # Date
            date_question = questions.filtered(lambda q: q.question_type in ['date', 'datetime'])
            date_value = ''
            if date_question:
                date_answer = response.user_input_line_ids.filtered(lambda l: l.question_id == date_question[0])
                if date_answer:
                    date_val = date_answer[0].value_date or date_answer[0].value_datetime
                    date_value = date_val.strftime('%Y-%m-%d') if date_val else ''
            if not date_value:
                date_value = response.create_date.strftime('%Y-%m-%d') if response.create_date else ''
            worksheet.write(row, col, date_value, cell_format)
            col += 1

            # Track matrix values for average calculation
            matrix_values = []
            
            # Process each question
            for question in questions:
                if question.question_type == 'matrix':
                    # Handle matrix questions - each row becomes a column
                    for matrix_row in question.matrix_row_ids.sorted('sequence'):
                        answer_line = response.user_input_line_ids.filtered(
                            lambda l: l.question_id == question and l.matrix_row_id == matrix_row
                        )
                        
                        if answer_line and answer_line.suggested_answer_id:
                            answer_value = answer_line.suggested_answer_id.value
                            try:
                                # Try to convert answer to number for average calculation
                                numeric_value = float(answer_value)
                                matrix_values.append(numeric_value)
                                worksheet.write(row, col, numeric_value, number_format)
                            except (ValueError, TypeError):
                                # If not a number, just write the text
                                worksheet.write(row, col, answer_value or '', cell_format)
                        else:
                            worksheet.write(row, col, '', cell_format)
                        col += 1
                        
                else:
                    # Handle other question types
                    answer_line = response.user_input_line_ids.filtered(lambda l: l.question_id == question)
                    
                    if answer_line:
                        if question.question_type in ['simple_choice', 'multiple_choice']:
                            answers = answer_line.mapped('suggested_answer_id.value')
                            worksheet.write(row, col, ', '.join(filter(None, answers)), cell_format)
                        elif question.question_type == 'text_box':
                            worksheet.write(row, col, answer_line[0].value_text_box or '', cell_format)
                        elif question.question_type == 'char_box':
                            worksheet.write(row, col, answer_line[0].value_char_box or '', cell_format)
                        elif question.question_type == 'numerical_box':
                            worksheet.write(row, col, answer_line[0].value_numerical_box or 0, number_format)
                        elif question.question_type == 'date':
                            date_val = answer_line[0].value_date
                            worksheet.write(row, col, date_val.strftime('%Y-%m-%d') if date_val else '', cell_format)
                        elif question.question_type == 'datetime':
                            date_val = answer_line[0].value_datetime
                            worksheet.write(row, col, date_val.strftime('%Y-%m-%d %H:%M:%S') if date_val else '', cell_format)
                        else:
                            worksheet.write(row, col, answer_line[0].display_name or '', cell_format)
                    else:
                        worksheet.write(row, col, '', cell_format)
                    col += 1

            # Calculate and write matrix average if there are matrix questions
            if matrix_questions and matrix_values:
                average = sum(matrix_values) / len(matrix_values)
                worksheet.write(row, col, round(average, 2), number_format)

            row += 1

        # Auto-adjust column widths
        for col in range(len(headers)):
            if col < 3:  # Basic info columns
                worksheet.set_column(col, col, 20)
            else:  # Question columns
                worksheet.set_column(col, col, 30)

        workbook.close()
        output.seek(0)

        # Save file
        file_data = base64.b64encode(output.read())
        file_name = f"{survey.title}_responses.xlsx"
        
        self.write({
            'excel_file': file_data,
            'file_name': file_name
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'survey.excel.export',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
            'context': {'default_survey_id': survey.id}
        }
