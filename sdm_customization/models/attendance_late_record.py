from datetime import date, timedelta
from collections import defaultdict
from odoo import api, fields, models

class AttendanceLateRecord(models.Model):
    _name = 'attendance.late.record'
    _rec_name = 'employee_id'
    _description = 'Daily Late Attendance Record'

    employee_id = fields.Many2one('hr.employee', string='Employee Name', required=True)
    date = fields.Date(string='Date', required=True, default=fields.Date.context_today)
    minutes_overdue = fields.Integer(string='Total Late Minutes', readonly=True)
    is_connect_sdm = fields.Boolean('Is SDM Connect', default=False)
    remarks = fields.Char('Remarks')

    _sql_constraints = [
        ('unique_employee_date', 'unique(employee_id, date)', 'A record already exists for this employee and date!')
    ]

    @api.model
    def send_weekly_summary_email(self):
        """Send weekly and cumulative summary (record count) of late attendance to managers"""
        today = fields.Date.today()
        first_day = today.replace(day=1)
        next_month = (first_day + timedelta(days=32)).replace(day=1)
        last_day = next_month - timedelta(days=1)

        # Fetch all records for current month
        records = self.search([
            ('date', '>=', first_day),
            ('date', '<=', last_day)
        ])

        if not records:
            return

        # Group data: employee -> week_number -> record count
        employee_data = defaultdict(lambda: defaultdict(int))
        for rec in records:
            week_number = ((rec.date.day - 1) // 7) + 1  # Week 1–5
            employee_data[rec.employee_id.name][f"W{week_number}"] += 1

        # Determine how many weeks exist dynamically (1–5)
        max_weeks = max([int(w[1:]) for emp in employee_data.values() for w in emp.keys()] or [1])

        # Header row
        headers = ''.join([
            f"<th style='border: 1px solid black; padding: 6px;background-color: #004080; color: white;'>W{i}</th>"
            for i in range(1, max_weeks + 1)
        ])
        headers += "<th style='border: 1px solid black; padding: 6px;background-color: #004080; color: white;'>Total</th>"

        # Data rows
        rows = ""
        for emp, weeks in employee_data.items():
            total = sum(weeks.values())
            week_cells = ''.join([
                f"<td style='border: 1px solid black; padding: 6px;'>{weeks.get(f'W{i}', 0)}</td>"
                for i in range(1, max_weeks + 1)
            ])
            rows += f"""
                    <tr>
                        <td style='border: 1px solid black; padding: 6px; text-align: left;'>{emp}</td>
                        {week_cells}
                        <td style='border: 1px solid black; padding: 6px; font-weight: bold;'>{total}</td>
                    </tr>
                """

        # Email content with fully bordered table
        subject = f"Late Attendance Summary (Record Count) - {today.strftime('%B %Y')}"
        body = f"""
            <p>Dear Managers,</p>
            <p>Please find below the weekly summary (number of late days) for <b>{today.strftime('%B %Y')}</b>:</p>
            <table style="border-collapse: collapse; width: 90%; text-align: center; font-family: Arial, sans-serif;">
                <thead style="background-color: #f2f2f2;">
                    <tr>
                        <th style='border: 1px solid black; padding: 6px; text-align: left;background-color: #004080; color: white;'>Employee</th>
                        {headers}
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
            <br/>
            <p>Regards,<br/><b>Odoo Attendance System</b></p>
            """

        # Send email to all users in the managers group
        managers = self.env.ref('prime_sol_custom.prime_group_managers').users
        if managers:
            mail_values = {
                'subject': subject,
                'body_html': body,
                'email_to': ','.join(managers.mapped('email')),
                'email_from': 'hr@primesystemsolutions.com',
            }
            self.env['mail.mail'].create(mail_values).send()

        return True
