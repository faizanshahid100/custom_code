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

    def calculate_employee_off_days(self, emp, start_date, end_date):
        if emp and not emp.resource_calendar_id:
            raise ValidationError(f"Employee {emp} has no working schedule assigned.")
        off_days = []
        working_hours = emp.resource_calendar_id
        working_days = set(attendance.dayofweek for attendance in working_hours.attendance_ids)
        date_range = [
            (start_date + timedelta(days=i))
            for i in range((end_date - start_date).days + 1)
        ]
        for date in date_range:
            if str(date.weekday()) not in working_days:
                off_days.append(date.day)
        return off_days

    def get_employee_leave_dates(self, emp, start_date, end_date):
        leave_records = self.env['hr.leave'].sudo().search([
            ('employee_id', '=', emp.id),
            ('state', '=', 'validate'),
            ('request_date_from', '>=', start_date),
            ('request_date_to', '<=', end_date),
        ])
        leave_dates = []
        for leave in leave_records:
            current_day = leave.request_date_from
            while current_day <= leave.request_date_to:
                leave_dates.append(current_day.day)
                current_day += timedelta(days=1)
        return leave_dates

    # For Excel Report
    my_xl_file = fields.Binary('Excel Report')
    file_name = fields.Char('File Name')

    def calculate_total_leaves_from_time_off(self, employee):
        # Get the current year
        current_year = date.today().year

        # Get all validated leave records for the employee within the current year
        leaves = self.env['hr.leave'].sudo().search([
            ('employee_id', '=', employee.id),
            ('state', '=', 'validate'),
            ('request_date_from', '>=', f'{current_year}-01-01'),
            ('request_date_from', '<', f'{current_year + 1}-01-01')
        ])

        # Check if there are any validated leave records; if not, return 0
        if not leaves:
            return 0

        # Sum the number_of_days_display field for all validated leave records within the current year
        total_leave = sum(leave.number_of_days_display for leave in leaves)
        return total_leave

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
            'font: bold on,height 220;align: wrap on,vert centre, horiz center; align: wrap yes,vert centre, horiz center;pattern: pattern solid, fore-colour blue;border: left thin,right thin,top thin,bottom thin')
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
        format_present = xlwt.easyxf(
            'font: height 200;'
            'align: wrap on, vert centre, horiz center;'
            'border: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, fore_color light_green;'
        )
        format_off_day = xlwt.easyxf(
            'font: height 200;'
            'align: wrap on, vert centre, horiz center;'
            'border: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, fore_color gray25;'
        )
        format_leave = xlwt.easyxf(
            'font: height 200;'
            'align: wrap on, vert centre, horiz center;'
            'border: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, fore_color yellow;'
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
        worksheet.col(6).width = 6000  # Level
        worksheet.col(7).width = 6000  # KPI Metric
        worksheet.col(8).width = 6000

        # Generate date range
        date_range = []
        current_date = self.date_from
        while current_date <= self.date_to:
            date_range.append(current_date)
            current_date += timedelta(days=1)

        # Set initial column index after KPI Metric (col 7)
        col_index = 8

        # Write headers for each date dynamically
        for date in date_range:
            date_str = date.strftime('%-d %b %Y') # Example: 1 Feb 2025
            worksheet.write_merge(3, 3, col_index, col_index + 3, date_str, table_heading_style)
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

        worksheet.write_merge(3, 3, 0, 7, 'Daily Progress Report', table_heading_style)
        worksheet.write(4, 0, 'Sr No.', table_heading_style)
        worksheet.write(4, 1, 'Employee Name', table_heading_style)
        worksheet.write(4, 2, 'Department', table_heading_style)
        worksheet.write(4, 3, 'Designation', table_heading_style)
        worksheet.write(4, 4, 'Contractor', table_heading_style)
        worksheet.write(4, 5, 'Gender', table_heading_style)
        worksheet.write(4, 6, 'Level', table_heading_style)
        worksheet.write(4, 7, 'KPI Metric', table_heading_style)


        if not self.department_id and not self.user_ids:
            users = self.env['res.users'].sudo().search([])
        elif self.department_id and not self.user_ids:
            users = self.env['res.users'].sudo().search([('department_id', '=', self.department_id.id)])
        elif self.user_ids and not self.department_id:
            users = self.user_ids
        progress_records = self.env['daily.progress'].sudo().search([('resource_user_id', 'in', users.ids), ('date_of_project', '>=', self.date_from), ('date_of_project', '<=', self.date_to)])
        progress_records_group = progress_records.read_group([('resource_user_id', 'in', users.ids), ('date_of_project', '>=', self.date_from), ('date_of_project', '<=', self.date_to)], ['resource_user_id'], ['resource_user_id'])

        if users:
            row = 5
            sr_no = 1
            for group in progress_records_group:
                progress = progress_records.sudo().search(group['__domain'])

                # Employee details
                worksheet.write(row, 0, _(sr_no), columns_left_bold_style)
                worksheet.write(row, 1, _(progress[0].resource_user_id.employee_id.sudo().name), columns_left_bold_style)
                worksheet.write(row, 2, _(progress[0].resource_user_id.employee_id.sudo().department_id.name), columns_left_bold_style)
                worksheet.write(row, 3, _(progress[0].resource_user_id.employee_id.sudo().job_id.name), columns_left_bold_style)
                worksheet.write(row, 4, _(progress[0].resource_user_id.employee_id.sudo().contractor.name if progress[0].resource_user_id.employee_id.sudo().contractor else ''), columns_left_bold_style)
                worksheet.write(row, 5, _(str(progress[0].resource_user_id.employee_id.sudo().gender).title() if progress[0].resource_user_id.employee_id.sudo().gender != False else ''), columns_left_bold_style)
                # worksheet.write(row, 5, _(dict(self.env['hr.employee'].fields_get(['gender'])['gender']['selection']).get(getattr(progress[0].resource_user_id.employee_id, 'gender', ''), '')), columns_left_bold_style)
                worksheet.write(row, 6, _(progress[0].resource_user_id.employee_id.sudo().level or ''), columns_left_bold_style)
                worksheet.write(row, 7, _(str(progress[0].resource_user_id.employee_id.sudo().kpi_measurement).title() or ''), columns_left_bold_style)

                # Start filling the dynamic columns after KPI Metric (Column 7)
                col_index = 8

                for date in date_range:
                    # Fetch progress record for the specific date and user
                    daily_record = progress.filtered(lambda p: p.date_of_project == date)
                    attendance = self.env['hr.attendance'].sudo().search([('employee_id', '=', progress[0].resource_user_id.employee_id.sudo().id), ('check_in', '>=', date), ('check_in', '<=', date)], limit=1)
                    off_day = self.calculate_employee_off_days(progress[0].resource_user_id.employee_id.sudo(), self.date_from, self.date_to)
                    leaves_day = self.get_employee_leave_dates(progress[0].resource_user_id.employee_id.sudo(), self.date_from, self.date_to)

                    if daily_record or attendance:
                        worksheet.write(row, col_index, daily_record.avg_resolved_ticket or 0, columns_center_bold_style)
                        worksheet.write(row, col_index + 1, daily_record.billable_hours or 0, columns_center_bold_style)
                        worksheet.write(row, col_index + 2, daily_record.no_calls_duration or 0, columns_center_bold_style)
                        worksheet.write(row, col_index + 3, 'Present', format_present)
                    else:
                        worksheet.write(row, col_index, 0, columns_center_bold_style)
                        worksheet.write(row, col_index + 1, 0, columns_center_bold_style)
                        worksheet.write(row, col_index + 2, 0, columns_center_bold_style)
                        if date.day in off_day:
                            worksheet.write(row, col_index + 3, 'Rest', format_off_day)
                        elif date.day in leaves_day:
                            worksheet.write(row, col_index + 3, 'Leave', format_leave)
                        else:
                            worksheet.write(row, col_index + 3, 'Absent', columns_center_bold_red_style)

                    col_index += 4  # Move to next set of columns

                # Add the MTD (Month-to-Date) column headers at the end
                worksheet.write_merge(3, 3, col_index, col_index + 4, 'MTD', yellow_table_heading_style)
                worksheet.write(4, col_index, 'Total Resolved', yellow_table_heading_style)
                worksheet.write(4, col_index + 1, 'Total Billable Hours', yellow_table_heading_style)
                worksheet.write(4, col_index + 2, 'Total No of Calls', yellow_table_heading_style)
                worksheet.write(4, col_index + 3, 'Total Presents', yellow_table_heading_style)
                worksheet.write(4, col_index + 4, 'Total Leaves', yellow_table_heading_style)
                # Set dynamic column widths (including MTD columns)
                for i in range(8, col_index + 5):  # +4 to include MTD columns
                    worksheet.col(i).width = 5000

                # Calculate and write MTD totals for the employee
                total_resolved = sum(progress.mapped('avg_resolved_ticket'))
                total_billable = sum(progress.mapped('billable_hours'))
                total_calls = sum(progress.mapped('no_calls_duration'))
                total_presents = sum(1 for p in progress if p.avg_resolved_ticket or p.billable_hours or p.no_calls_duration)

                worksheet.write(row, col_index, total_resolved, columns_center_bold_style)
                worksheet.write(row, col_index + 1, total_billable, columns_center_bold_style)
                worksheet.write(row, col_index + 2, total_calls, columns_center_bold_style)
                worksheet.write(row, col_index + 3, total_presents, columns_center_bold_style) # yellow_table_heading_style
                worksheet.write(row, col_index + 4, self.calculate_total_leaves_from_time_off(progress[0].resource_user_id.employee_id.sudo()), columns_center_bold_style)


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