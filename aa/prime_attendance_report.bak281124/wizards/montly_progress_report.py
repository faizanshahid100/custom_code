from odoo import api, fields, models, registry, _
from io import BytesIO
import base64
import datetime
from datetime import timedelta
import xlsxwriter
from odoo.exceptions import ValidationError, UserError


class MonthlyProgressReport(models.TransientModel):
    _name = 'monthly.progress.report'
    _description = 'Monthly Progress Report'

    @api.model
    def default_get(self, default_fields):
        res = super(MonthlyProgressReport, self).default_get(default_fields)
        today = datetime.date.today()
        first = today.replace(day=1)
        last_month_first = (today - timedelta(days=today.day)).replace(day=1)
        last_month = first - datetime.timedelta(days=1)
        res.update({
            'date_from': last_month_first or False,
            'date_to': last_month or False
        })
        return res

    user_ids = fields.Many2many('res.users', string='Users')
    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')

    # def action_generate_report(self):
    #     if self.date_from > self.date_to:
    #         raise UserError('End Date must be greater than or equal to Start Date.')
    #
    #     # Fetch and process records
    #     records = self._get_records(self.user_ids, self.date_from, self.date_to)
    #     report_data = self._process_records(records)
    #     # Generate Excel report
    #     return self._generate_excel_report(report_data)

    def action_generate_report(self):
        if self.date_from > self.date_to:
            raise UserError('End Date must be greater than or equal to Start Date.')

        # Fetch records and all users
        records, all_users = self._get_records(self.user_ids, self.date_from, self.date_to)

        # Process records, including all users
        report_data = self._process_records(records, all_users)

        # Generate Excel report
        return self._generate_excel_report(report_data)

    # def _get_records(self, users, date_from, date_to):
    #     Replace with your actual data fetching logic
        # print(11111111111111, users , len(users))
        # return self.env['weekly.progress'].search([('resource_user_id', 'in', users.ids),
        #                                            ('date_of_project', '>=', date_from),
        #                                            ('date_of_project', '<=', date_to)])

    def _get_records(self, users, date_from, date_to):
        # Fetch records for users with data in the specified date range
        records = self.env['weekly.progress'].search([
            ('resource_user_id', 'in', users.ids),
            ('date_of_project', '>=', date_from),
            ('date_of_project', '<=', date_to)
        ])
        # Also return the list of users without filtering by records
        all_users = self.env['res.users'].search([])
        return records, all_users

    # def _process_records(self, records):
    #     # Process the records to calculate weekly progress
    #     result = {}
    #
    #     for record in records:
    #         user = record.resource_user_id
    #         week_key = record.formatted_date  # Example: '24-W30'
    #
    #         # Extract year and week number from '24-W30' or '24-W24'
    #         try:
    #             year, week_num = week_key.split('-W')
    #             year = f"20{year}"  # Convert to full year, e.g., '2024'
    #             week_num = int(week_num)
    #         except ValueError:
    #             # Handle cases where the format is not as expected
    #             continue
    #
    #         # Compute the start and end dates of the week
    #         try:
    #             date_str = f'{year}-W{week_num}-1'  # Monday of the given week
    #             week_start_date = datetime.datetime.strptime(date_str, "%Y-W%W-%w")
    #             week_label = f"{year[-2:]}-W{week_num:02d}"
    #         except ValueError:
    #             # Handle invalid date formats
    #             continue
    #
    #         # Initialize user data if not present
    #         if user not in result:
    #             result[user] = {}
    #
    #         # Initialize week data if not present for the user
    #         if week_label not in result[user]:
    #             result[user][week_label] = {
    #                 'total_tickets': 0,
    #                 'resolved_tickets': 0,
    #                 'avg_time': 0,
    #                 'csat': 0,
    #                 'billable_hours': 0,
    #                 'no_call': 0,
    #             }
    #
    #         # Update totals
    #         if record:
    #             result[user][week_label]['total_tickets'] += record.ticket_assigned_new
    #             result[user][week_label]['resolved_tickets'] += record.avg_resolved_ticket
    #             result[user][week_label]['avg_time'] += record.avg_resolution_time
    #             result[user][week_label]['csat'] += record.csat_new
    #             result[user][week_label]['billable_hours'] += record.billable_hours
    #             result[user][week_label]['no_call'] += record.no_calls_duration
    #
    #     # Return the structured result
    #     print(22222222222222222222222, result)
    #     return result

    def _process_records(self, records, all_users):
        result = {}

        # Initialize all users in the result with empty week data
        for user in all_users:
            result[user] = {}

        for record in records:
            user = record.resource_user_id
            week_key = record.formatted_date  # Example: '24-W30'
            try:
                year, week_num = week_key.split('-W')
                year = f"20{year}"  # Convert to full year, e.g., '2024'
                week_num = int(week_num)
            except ValueError:
                continue

            # Compute the start date of the week
            try:
                date_str = f'{year}-W{week_num}-1'  # Monday of the given week
                week_start_date = datetime.datetime.strptime(date_str, "%Y-W%W-%w")
                week_label = f"{year[-2:]}-W{week_num:02d}"
            except ValueError:
                continue

            # Initialize week data for each user, if not already present
            if week_label not in result[user]:
                result[user][week_label] = {
                    'total_tickets': 0,
                    'resolved_tickets': 0,
                    'avg_time': 0,
                    'csat': 0,
                    'billable_hours': 0,
                    'no_call': 0,
                }

            # Update metrics if record exists
            if record:
                result[user][week_label]['total_tickets'] += record.ticket_assigned_new
                result[user][week_label]['resolved_tickets'] += record.avg_resolved_ticket
                result[user][week_label]['avg_time'] += record.avg_resolution_time
                result[user][week_label]['csat'] += record.csat_new
                result[user][week_label]['billable_hours'] += record.billable_hours
                result[user][week_label]['no_call'] += record.no_calls_duration

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
        totalheader_format = workbook.add_format({
            'bold': True,
            'rotation': 90,
            'fg_color': '#BEBEBE',
            'border': 1,
        })

        # Title
        worksheet.merge_range('B2:Y3', 'Monthly Progress Report (Week Wise)', header_format)
        worksheet.write('B5', "Dare From :")
        worksheet.write('C5', self.date_from, date_format)
        worksheet.write('B6', "Date To :")
        worksheet.write('C6', self.date_to, date_format)

        # Collect all week labels
        week_labels = sorted({week for weeks in data.values() for week in weeks})
        worksheet.merge_range(6, 0, 6, 2, '', week_format)
        worksheet.merge_range(6, 3, 6, 6, 'Weekly Target', week_format)
        # Write merged headers for weeks
        week_col_start = 7
        for week in week_labels:
            week_col_end = week_col_start + 5  # Total of 3 columns per week
            worksheet.merge_range(6, week_col_start, 6, week_col_end, week, week_format)
            week_col_start = week_col_end + 1

        worksheet.merge_range(6, week_col_start, 6, week_col_start + 5, 'Monthly', workbook.add_format({'bold': True,
                                                                                                        'align': 'center',
                                                                                                        'fg_color': '#8EA9DB',
                                                                                                        'border': 1}))

        # Write subheaders for metrics
        headers = ['ID', 'Employee Name', 'Department']
        total_header = ['Resolved', 'Avg Time', 'CAST %', 'Billable Hours']
        subheaders = ['Tickets Assigned', 'Tickets Resolved', 'Avg Time', 'CSAT %', 'Billable Hours', 'No of Calls Attend']
        totalheader = ['Monthly Assigned', 'Monthly Resolved', 'Monthly Avg time', 'Monthly CSAT%', 'Monthly Billable Hours', 'Monthly No of Call Attend']


        worksheet.write_row(7, 0, headers, headers_format)
        worksheet.write_row(7, 3, total_header, total_format)
        worksheet.write_row(7, 7, subheaders * len(week_labels), subheaders_format)
        worksheet.write_row(7, 7 + (len(week_labels) * 6), totalheader, totalheader_format)

        worksheet.set_column('A:A', 3)
        worksheet.set_column('B:B', 25)
        worksheet.set_column('C:C', 15)
        worksheet.set_column('D:BB', 4)
        worksheet.set_row(7, 140)

        red_format = workbook.add_format({'bg_color': '#FF6666'})  # Light red background

        # Write user data
        row = 8
        for user, weeks in data.items():
            monthly_totals = {
                'total_tickets': 0,
                'resolved_tickets': 0,
                'avg_time': 0,
                'csat': 0,
                'billable_hours': 0,
                'no_call': 0
            }
            row_data = [user.id, user.name, user.employee_id.department_id.name, user.employee_id.ticket_resolved, user.employee_id.avg_resolution_time, user.employee_id.CAST, user.employee_id.billable_hours]

            for week in week_labels:
                metrics = weeks.get(week, {'total_tickets': 0, 'resolved_tickets': 0, 'avg_time': 0, 'csat': 0, 'billable_hours': 0, 'no_call': 0})
                row_data.extend([
                    metrics['total_tickets'],
                    metrics['resolved_tickets'],
                    metrics['avg_time'],
                    metrics['csat'],
                    metrics['billable_hours'],
                    metrics['no_call'],
                ])
                # Accumulate monthly totals
                monthly_totals['total_tickets'] += metrics['total_tickets']
                monthly_totals['resolved_tickets'] += metrics['resolved_tickets']
                monthly_totals['avg_time'] += metrics['avg_time']
                monthly_totals['csat'] += metrics['csat']
                monthly_totals['billable_hours'] += metrics['billable_hours']
                monthly_totals['no_call'] += metrics['no_call']

            row_data.extend([
                monthly_totals['total_tickets'],
                monthly_totals['resolved_tickets'],
                monthly_totals['avg_time'],
                monthly_totals['csat'],
                monthly_totals['billable_hours'],
                monthly_totals['no_call'],
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
            'name': 'Weekly_Progress_Report.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(output.read()),
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }
