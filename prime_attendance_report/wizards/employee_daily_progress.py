from odoo import models, fields, api, _
from datetime import datetime, date, timedelta
import time
import datetime
import calendar
from odoo.exceptions import AccessError, UserError, ValidationError
import xlwt
import base64
from io import BytesIO


class EmployeeDailyProgress(models.TransientModel):
    _name = "employee.daily.progress"
    _description = "Employee Daily Progress Report"

    @api.model
    def default_get(self, default_fields):
        res = super(EmployeeDailyProgress, self).default_get(default_fields)
        today = datetime.date.today()

        first_day_current_month = today.replace(day=1)  # 1st day of the current month
        yesterday = today - datetime.timedelta(days=1)  # Yesterday (today - 1 day)

        res.update({
            'date_from': first_day_current_month or False,
            'date_to': yesterday or False
        })
        return res

    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    department_id = fields.Many2one('hr.department', string='Department')
    user_ids = fields.Many2many('res.users', string='Users')

    @api.constrains('department_id', 'user_ids')
    def _check_department_or_users(self):
        """ Ensure that either department_id or user_ids is selected, but NOT both at the same time """
        for record in self:
            if record.department_id and record.user_ids:
                raise ValidationError(_("You can either select a Department or specific Users, but not both."))

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        """ Validate the date range """
        for record in self:
            if record.date_from > record.date_to:
                raise ValidationError(_("The 'Date From' must be before or equal to 'Date To'."))

    # For Excel Report
    my_xl_file = fields.Binary('Excel Report')
    file_name = fields.Char('File Name')

    def action_generate_report(self):
        workbook = xlwt.Workbook(encoding='utf-8')
        worksheet = workbook.add_sheet('Daily Progress Report', cell_overwrite_ok=True)
        heading_style = xlwt.easyxf(
            'font: bold on,height 300;align: wrap on,vert centre, horiz center; align: wrap yes,vert centre, horiz center;pattern: pattern solid, fore-colour aqua;border: left thin,right thin,top thin,bottom thin')
        main_table_heading_style = xlwt.easyxf(
            'font: bold on,height 220;align: wrap on,vert centre, horiz center; align: wrap yes,vert centre, horiz center;pattern: pattern solid, fore-colour light_green;border: left thin,right thin,top thin,bottom thin')
        table_heading_style = xlwt.easyxf(
            'font: bold on,height 220;align: wrap on,vert centre, horiz center; align: wrap yes,vert centre, horiz center;pattern: pattern solid, fore-colour aqua;border: left thin,right thin,top thin,bottom thin')
        mtd_table_heading_style = xlwt.easyxf(
            'font: bold on,height 220;align: wrap on,vert centre, horiz center; align: wrap yes,vert centre, horiz center;pattern: pattern solid, fore-colour teal;border: left thin,right thin,top thin,bottom thin')
        yellow_table_heading_style = xlwt.easyxf(
            'font: bold on,height 220;align: wrap on,vert centre, horiz center; align: wrap yes,vert centre, horiz center;pattern: pattern solid, fore-colour yellow;border: left thin,right thin,top thin,bottom thin')
        plum_table_heading_style = xlwt.easyxf(
            'font: bold on,height 220;align: wrap on,vert centre, horiz center; align: wrap yes,vert centre, horiz center;pattern: pattern solid, fore-colour plum;border: left thin,right thin,top thin,bottom thin')
        dept_heading_style = xlwt.easyxf(
            'font: bold on,height 220;align: wrap on,vert centre, horiz left; align: wrap yes,vert centre;pattern: pattern solid, fore-colour light_green;border: left thin,right thin,top thin,bottom thin')
        columns_center_bold_style = xlwt.easyxf(
            'font: height 200;align: wrap on,vert centre, horiz center; align: wrap yes,vert centre;  border: left thin,right thin,top thin,bottom thin')
        columns_center_bold_red_style = xlwt.easyxf(
            'font: height 200;'
            'align: wrap on, vert centre, horiz center;'
            'border: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, fore-colour red;'
        )
        columns_center_bold_green_style = xlwt.easyxf(
            'font: height 200;'
            'align: wrap on, vert centre, horiz center;'
            'border: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, fore-colour green;'
        )
        top_center_bold_style = xlwt.easyxf(
            'font: bold on, height 200;align: wrap on,vert centre, horiz left; align: wrap yes,vert centre;')
        columns_right_bold_style = xlwt.easyxf(
            'font: height 200;align: wrap on,vert centre, horiz right; align: wrap yes,vert centre; border: left thin,right thin,top thin,bottom thin')
        table_right_heading_style = xlwt.easyxf(
            'font: bold on,height 220;align: wrap on,vert centre, horiz right; align: wrap yes,vert centre, horiz right;pattern: pattern solid, fore-colour aqua;border: left thin,right thin,top thin,bottom thin')
        columns_left_bold_style = xlwt.easyxf(
            'font: height 200;align: wrap on,vert centre, horiz left; align: wrap yes,vert centre; border: left thin,right thin,top thin,bottom thin')

        worksheet.col(0).width = 3000  # Sr No.
        worksheet.col(1).width = 7000  # Employee Name
        worksheet.col(2).width = 4500  # Department
        worksheet.col(3).width = 7000  # Designation
        worksheet.col(4).width = 5000  # Contractor
        worksheet.row(2).height = 400
        worksheet.row(3).height = 400
        worksheet.row(4).height = 500
        worksheet.col(5).width = 5000  # Gender
        worksheet.col(6).width = 6000
        worksheet.col(7).width = 6000
        worksheet.col(8).width = 6000

        # Generate date range
        date_range = []
        current_date = self.date_from
        while current_date <= self.date_to:
            date_range.append(current_date)
            current_date += timedelta(days=1)

        # Set initial column index after Gender (col 5)
        col_index = 6

        # Write headers for each date dynamically
        for date in date_range:
            date_str = date.strftime('%-d %b %Y') # Example: 1 Feb 2025
            worksheet.write_merge(3, 3, col_index, col_index + 3, date_str, plum_table_heading_style)
            worksheet.write(4, col_index, 'Ticket Resolved', yellow_table_heading_style)
            worksheet.write(4, col_index + 1, 'Billable Hours', yellow_table_heading_style)
            worksheet.write(4, col_index + 2, 'No of Calls', yellow_table_heading_style)
            worksheet.write(4, col_index + 3, 'Attendance', yellow_table_heading_style)
            col_index += 4  # Move to the next set of columns

        # Set dynamic column widths
        for i in range(6, col_index):
            worksheet.col(i).width = 4000

        for wizard in self:
            pass
        worksheet.write_merge(1, 1, 0, 0, _('From Date'), top_center_bold_style)
        worksheet.write_merge(1, 1, 1, 1, _(self.date_from.strftime('%d-%m-%Y')), top_center_bold_style)
        worksheet.write_merge(2, 2, 0, 0, _('Till Date'), top_center_bold_style)
        worksheet.write_merge(2, 2, 1, 1, _(self.date_to.strftime('%d-%m-%Y')), top_center_bold_style)

        worksheet.write_merge(3, 3, 0, 5, 'Daily Progress Report', table_heading_style)
        worksheet.write(4, 0, 'Sr No.', table_heading_style)
        worksheet.write(4, 1, 'Employee Name', table_heading_style)
        worksheet.write(4, 2, 'Department', table_heading_style)
        worksheet.write(4, 3, 'Designation', table_heading_style)
        worksheet.write(4, 4, 'Contractor', table_heading_style)
        worksheet.write(4, 5, 'Gender', table_heading_style)


        if not self.department_id and not self.user_ids:
            users = self.env['res.users'].search([])
        elif self.department_id and not self.user_ids:
            users = self.env['res.users'].search([('department_id', '=', self.department_id.id)])
        elif self.user_ids and not self.department_id:
            users = self.user_ids
        progress_records = self.env['daily.progress'].search([('resource_user_id', 'in', users.ids), ('date_of_project', '>=', self.date_from), ('date_of_project', '<=', self.date_to)])
        progress_records_group = progress_records.read_group([('resource_user_id', 'in', users.ids), ('date_of_project', '>=', self.date_from), ('date_of_project', '<=', self.date_to)], ['resource_user_id'], ['resource_user_id'])

        if progress_records:
            row = 5
            sr_no = 1
            for group in progress_records_group:
                progress = progress_records.search(group['__domain'])

                # Employee details
                worksheet.write(row, 0, _(sr_no), columns_left_bold_style)
                worksheet.write(row, 1, _(progress[0].resource_user_id.employee_id.name), columns_left_bold_style)
                worksheet.write(row, 2, _(progress[0].resource_user_id.employee_id.department_id.name), columns_left_bold_style)
                worksheet.write(row, 3, _(progress[0].resource_user_id.employee_id.job_id.name), columns_left_bold_style)
                worksheet.write(row, 4, _(progress[0].resource_user_id.employee_id.contractor or ''), columns_left_bold_style)
                worksheet.write(row, 5, _(dict(self.env['hr.employee'].fields_get(['gender'])['gender']['selection']).get(progress[0].resource_user_id.employee_id.gender, '')), columns_left_bold_style)

                # Start filling the dynamic columns after Gender (Column 6)
                col_index = 6

                for date in date_range:
                    # Fetch progress record for the specific date and user
                    daily_record = progress.filtered(lambda p: p.date_of_project == date)

                    if daily_record:
                        worksheet.write(row, col_index, daily_record.avg_resolved_ticket or 0, columns_center_bold_style)
                        worksheet.write(row, col_index + 1, daily_record.billable_hours or 0, columns_center_bold_style)
                        worksheet.write(row, col_index + 2, daily_record.no_calls_duration or 0, columns_center_bold_style)
                        worksheet.write(row, col_index + 3, 'Present', columns_center_bold_green_style)
                    else:
                        worksheet.write(row, col_index, 0, columns_center_bold_style)
                        worksheet.write(row, col_index + 1, 0, columns_center_bold_style)
                        worksheet.write(row, col_index + 2, 0, columns_center_bold_style)
                        worksheet.write(row, col_index + 3, 'Absent', columns_center_bold_red_style)

                    col_index += 4  # Move to next set of columns

                # Add the MTD (Month-to-Date) column headers at the end
                worksheet.write_merge(3, 3, col_index, col_index + 3, 'MTD', mtd_table_heading_style)
                worksheet.write(4, col_index, 'Total Resolved', mtd_table_heading_style)
                worksheet.write(4, col_index + 1, 'Total Billable Hours', mtd_table_heading_style)
                worksheet.write(4, col_index + 2, 'Total No of Calls', mtd_table_heading_style)
                worksheet.write(4, col_index + 3, 'Total Presents', mtd_table_heading_style)
                # Set dynamic column widths (including MTD columns)
                for i in range(6, col_index + 4):  # +4 to include MTD columns
                    worksheet.col(i).width = 5000

                # Calculate and write MTD totals for the employee
                total_resolved = sum(progress.mapped('avg_resolved_ticket'))
                total_billable = sum(progress.mapped('billable_hours'))
                total_calls = sum(progress.mapped('no_calls_duration'))
                total_presents = sum(1 for p in progress if p.avg_resolved_ticket or p.billable_hours or p.no_calls_duration)

                worksheet.write(row, col_index, total_resolved, columns_center_bold_style)
                worksheet.write(row, col_index + 1, total_billable, columns_center_bold_style)
                worksheet.write(row, col_index + 2, total_calls, columns_center_bold_style)
                worksheet.write(row, col_index + 3, total_presents, yellow_table_heading_style)


                sr_no+=1
                worksheet.row(row).height = 400
                row += 1
                # # Last Line of Total Amount
                # worksheet.write(row, 0, _(''), table_heading_style)
                # worksheet.write(row, 1, _(''), table_heading_style)
                # worksheet.write(row, 2, _(''), table_heading_style)
                # worksheet.write(row, 3, _(''), table_heading_style)
                # worksheet.write(row, 4, _(''), table_heading_style)
                # worksheet.write(row, 5, _(''), table_heading_style)


        else:
            raise ValidationError('No Record is available regarding the Parameters.')
        stream = BytesIO()
        workbook.save(stream)
        excel_file = base64.encodebytes(stream.getvalue())
        wizard.my_xl_file = excel_file
        wizard.file_name = 'Daily_Progress.xls'
        stream.close()
        return {
            'type': 'ir.actions.act_url',
            'url': 'web/content/?model=employee.daily.progress&field=my_xl_file&download=true&id=%s&filename=%s' % (
                self.id, 'Daily_Progress.xls'),
        }