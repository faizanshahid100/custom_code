from odoo import api, fields, models, registry, _
from datetime import date, timedelta
from odoo.exceptions import ValidationError

class MeetingSummaryWizard(models.TransientModel):
    _name = 'meeting.summary'
    _description = 'Meeting Summary Wizard'

    @api.model
    def default_get(self, default_fields):
        res = super(MeetingSummaryWizard, self).default_get(default_fields)
        today = date.today()

        # First day of the current year
        first_day_current_year = today.replace(month=1, day=1)

        # Yesterday (today - 1 day)
        yesterday = today - timedelta(days=1)

        res.update({
            'date_from': first_day_current_year or False,
            'date_to': today or False
        })
        return res

    date_from = fields.Date(string="Start Date", required=True)
    date_to = fields.Date(string="End Date", required=True)
    partner_id = fields.Many2one('res.partner', string="Partner", required=True, domain=[('is_company','=', True)])

    def action_confirm(self):
        # Optional: Clear existing summaries
        self.env['meeting.attendance.summary'].search([]).unlink()

        # Build search domain if filtering is needed
        domain = []
        if self.partner_id:
            # Add conditions for partner_id and date range
            domain.append(('meeting_id.client_id', '=', self.partner_id.id))
            domain.append(('meeting_id.date', '>=', self.date_from))
            domain.append(('meeting_id.date', '<=', self.date_to))

        details = self.env['meeting.details'].search(domain)

        # Initialize dictionaries to track meeting counts
        employee_meeting_count = {}
        employee_attended_count = {}

        # Iterate over the details to count total and attended meetings for each employee
        for detail in details:
            employee_id = detail.employee_id.id

            # Count total meetings
            if employee_id not in employee_meeting_count:
                employee_meeting_count[employee_id] = 0
            employee_meeting_count[employee_id] += 1

            # Count attended meetings (where is_present is True)
            if detail.is_present:
                if employee_id not in employee_attended_count:
                    employee_attended_count[employee_id] = 0
                employee_attended_count[employee_id] += 1

        # Initialize a set to track processed employee_ids
        processed_employee_ids = set()

        for detail in details:
            employee_id = detail.employee_id.id

            # Skip if the employee_id has already been processed
            if employee_id in processed_employee_ids:
                continue

            # Add the employee_id to the set to avoid duplicates
            processed_employee_ids.add(employee_id)

            # Get the total meetings and attended meetings counts for the employee
            total_meetings = employee_meeting_count.get(employee_id, 0)
            attended_meetings = employee_attended_count.get(employee_id, 0)

            # Create a new summary entry with total and attended meetings count
            self.env['meeting.attendance.summary'].create({
                'employee_id': employee_id,
                'partner_id': detail.employee_id.contractor.id if detail.employee_id.contractor else '',
                'level': detail.employee_id.level if detail.employee_id.level else '',
                'kpi_measurement': detail.employee_id.kpi_measurement,
                'job_id': detail.employee_id.job_id.id if detail.employee_id.job_id else '',
                'total_meetings': total_meetings,  # Total meetings count
                'attended_meetings': attended_meetings,  # Attended meetings count
            })

        return {
            'name': 'Meeting Attendance Summary',
            'type': 'ir.actions.act_window',
            'res_model': 'meeting.attendance.summary',
            'view_mode': 'tree',
            'target': 'current',  # This makes it full-screen, not a popup
            'domain': [],  # Optional: you can pass specific domain if needed
        }
