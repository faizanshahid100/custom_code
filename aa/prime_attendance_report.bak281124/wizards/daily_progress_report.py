from odoo import api, fields, models, registry, _
from io import BytesIO
import base64
import datetime
import xlsxwriter


class DailyProgressReport(models.TransientModel):
    _name = 'daily.progress.report'
    _description = 'Daily Progress Report'

    @api.model
    def default_get(self, default_fields):
        res = super(DailyProgressReport, self).default_get(default_fields)
        today = datetime.date.today()
        res.update({
            'date_of': today or False
        })
        return res

    user_ids = fields.Many2many('res.users', string='Users')
    date_of = fields.Date(string='Date of')

    def action_generate_report(self):
        # Fetch records and all users
        records, all_users = self._get_records(self.user_ids, self.date_of)

        # Process records, including all users
        report_data = self._process_records(records, all_users)

        # Generate Excel report
        return self._generate_excel_report(report_data)

    def _get_records(self, users, date_of):
        # Fetch records for users with data in the specified date range
        records = self.env['daily.progress'].search([
            ('resource_user_id', 'in', users.ids),
            ('date_of_project', '=', date_of),
        ])
        # Also return the list of users without filtering by records
        all_users = self.env['res.users'].search([])
        return records, all_users

    def _process_records(self, records, all_users):
        result = {}

        # Initialize all users in the result with empty daily data
        for user in all_users:
            result[user] = {}

        for record in records:
            user = record.resource_user_id
            daily_key = record.date_of_project.strftime('%Y-%m-%d')  # Group by specific date (e.g., '2024-11-17')

            # Initialize daily data for each user, if not already present
            if daily_key not in result[user]:
                result[user][daily_key] = {
                    'total_tickets': 0,
                    'resolved_tickets': 0,
                    'avg_time': 0,
                    'csat': 0,
                    'billable_hours': 0,
                    'no_call': 0,
                }

            # Update metrics if record exists
            result[user][daily_key]['total_tickets'] += record.ticket_assigned_new
            result[user][daily_key]['resolved_tickets'] += record.avg_resolved_ticket
            result[user][daily_key]['avg_time'] += record.avg_resolution_time
            result[user][daily_key]['csat'] += record.csat_new
            result[user][daily_key]['billable_hours'] += record.billable_hours
            result[user][daily_key]['no_call'] += record.no_calls_duration

        return result

    def _generate_excel_report(self, data):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Monthly Progress Report')

        header_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'size': 16,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': '#8EA9DB',
        })
        date_format = workbook.add_format({
            'num_format': 'dd/mm/yy',
            'align': 'left',
            "valign": 'vcenter',
            'font_size': '11',
        })
        week_format = workbook.add_format({
            'align': 'center',
            "valign": 'vcenter',
            'bold': True,
            'fg_color': '#BEBEBE',
            'border': 1
        })
        headers_format = workbook.add_format({
            'bold': True,
            'fg_color': '#BEBEBE',
            'border': 1,
        })
        subheaders_format = workbook.add_format({
            'bold': True,
            'rotation': 90,
            'fg_color': '#8EA9DB',
            'border': 1,
        })
        total_format = workbook.add_format({
            'bold': True,
            'rotation': 90,
            'fg_color': '#BEBEBE',
            'border': 1,
        })

        # Title
        worksheet.merge_range('B2:M3', 'Daily Progress Report', header_format)
        worksheet.write('B5', "Dare :")
        worksheet.write('C5', self.date_of, date_format)

        # Collect all week labels
        daily_labels = sorted({day for days in data.values() for day in days})

        worksheet.merge_range(6, 0, 6, 2, '', week_format)
        worksheet.merge_range(6, 3, 6, 6, 'Daily Target', week_format)
        # Write merged headers for weeks
        week_col_start = 7
        for week in daily_labels:
            week_col_end = week_col_start + 5  # Total of 3 columns per week
            worksheet.merge_range(6, week_col_start, 6, week_col_end, week, week_format)
            week_col_start = week_col_end + 1

        # Write subheaders for metrics
        headers = ['ID', 'Employee Name', 'Department']
        total_header = ['Resolved', 'Avg Time', 'CAST %', 'Billable Hours']
        subheaders = ['Tickets Assigned', 'Tickets Resolved', 'Avg Time', 'CSAT %', 'Billable Hours', 'No of Calls Attend']

        worksheet.write_row(7, 0, headers, headers_format)
        worksheet.write_row(7, 3, total_header, total_format)
        worksheet.write_row(7, 7, subheaders * len(daily_labels), subheaders_format)

        worksheet.set_column('A:A', 3)
        worksheet.set_column('B:B', 25)
        worksheet.set_column('C:C', 15)
        worksheet.set_column('D:BB', 4)
        worksheet.set_row(7, 140)

        red_format = workbook.add_format({'bg_color': '#FF6666'})  # Light red background

        # Write user data
        row = 8
        for user, weeks in data.items():
            row_data = [user.id, user.name, user.employee_id.department_id.name, user.employee_id.d_ticket_resolved, user.employee_id.d_avg_resolution_time, user.employee_id.d_CAST, user.employee_id.d_billable_hours]

            for week in daily_labels:
                metrics = weeks.get(week, {'total_tickets': 0, 'resolved_tickets': 0, 'avg_time': 0, 'csat': 0, 'billable_hours': 0, 'no_call': 0})
                row_data.extend([
                    metrics['total_tickets'],
                    metrics['resolved_tickets'],
                    metrics['avg_time'],
                    metrics['csat'],
                    metrics['billable_hours'],
                    metrics['no_call'],
                ])
            a = 8
            b = 9
            c = 10
            d = 11
            for col_num, value in enumerate(row_data):
                if col_num == a:
                    if row_data[3] > value:
                        worksheet.write(row, col_num, value, red_format)
                    else:
                        worksheet.write(row, col_num, value)
                    a += 5

                elif col_num == b:
                    if row_data[4] > value:
                        worksheet.write(row, col_num, value, red_format)
                    else:
                        worksheet.write(row, col_num, value)
                    b += 5

                elif col_num == c:
                    if row_data[5] > value:
                        worksheet.write(row, col_num, value, red_format)
                    else:
                        worksheet.write(row, col_num, value)
                    c += 5
                elif col_num == d:
                    if row_data[6] > value:
                        worksheet.write(row, col_num, value, red_format)
                    else:
                        worksheet.write(row, col_num, value)
                    d += 5

                else:
                    worksheet.write(row, col_num, value)

            row += 1

        workbook.close()
        output.seek(0)

        # Create the attachment
        attachment = self.env['ir.attachment'].create({
            'name': 'Daily_Progress_Report.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(output.read()),
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }
