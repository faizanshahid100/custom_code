from odoo import models, fields, api

class ConnectWiseAttendance(models.Model):
    _name = 'connect.wise.attendance'
    _description = 'Connect Wise Attendance Form'

    name = fields.Char('Name', required=True)
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True)
    date = fields.Date('Date', default=fields.Date.today)
    
    # Tag fields
    tag_urgent = fields.Boolean('Urgent')
    tag_priority = fields.Boolean('Priority')
    tag_completed = fields.Boolean('Completed')
    tag_pending = fields.Boolean('Pending')
    tag_approved = fields.Boolean('Approved')
    tag_rejected = fields.Boolean('Rejected')
    tag_review = fields.Boolean('Review')
    tag_draft = fields.Boolean('Draft')
    tag_active = fields.Boolean('Active')
    tag_inactive = fields.Boolean('Inactive')
    
    notes = fields.Text('Notes')
