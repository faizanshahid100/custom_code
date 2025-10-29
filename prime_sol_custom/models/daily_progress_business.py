import math
import logging
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import date

_logger = logging.getLogger(__name__)


class DailyProgress(models.Model):
    _name = "daily.progress.business"
    _inherit = "mail.thread"
    _description = "Daily Progress Business"
    _rec_name = 'resource_user_id'

    resource_user_id = fields.Many2one('res.users', string='Resource Name *', default=lambda self: self.env.user.id)
    date_of_project = fields.Date("Today Date", required=True, default=lambda self: date.today())
    finance_area = fields.Selection([
        ('fpna', 'Financial Planning & Analysis'),
        ('ap', 'Accounts Payable'),
        ('ar', 'Accounts Receivable'),
        ('sa', 'Senior Accountant'),
    ], default='fpna', string="Finance Area", required=True)
    # Financial Planning & Analysis
    project = fields.Char(string='Task/Project')
    is_deadline_met = fields.Boolean(string='Deadline Met?')
    is_week_meeting = fields.Boolean(string='Weekly LM Meeting')
    comments = fields.Char(string='Comments')
    manager_comment = fields.Selection([
        ('extremely_satisfied', 'Extremely Satisfied'),
        ('satisfied', 'Satisfied'),
        ('neutral', 'Neutral'),
        ('not_satisfied', 'Not Satisfied'),
        ('extremely_not_satisfied', 'Extremely Not Satisfied'),
    ], default='extremely_satisfied', string="Manager Comment")

    # Accounts Payable
    invoice_count = fields.Integer(string="No. of Invoices")
    pending_approval_count = fields.Integer(string="Pending Approvals")
    closed_ticket_count = fields.Integer(string="Tickets Closed")

    # Accounts Receivable
    number_of_calls = fields.Integer(string="Number of Calls")
    bad_debt = fields.Integer(string="Bad Debt(Assigned)")
    recovery_of_bad_debt = fields.Integer(string="Recovery of Bad Debt")



    week_of_year = fields.Char(string="Week of the Year", compute="_compute_week_of_year", store=True)
    year_of_kpi = fields.Char(string="KPI Year")

    # Senior Accountant
    is_accrued_expenses = fields.Boolean(string='Accrued Expenses      | 3rd Business Day')
    is_decommissioning = fields.Boolean(string='Decommissioning       | -2 Business Day')
    is_leases = fields.Boolean(string='Leases                | 1st Business Day')
    is_other_current_assets = fields.Boolean(string='Other Current Assets  | 3rd Business Day')
    is_prepaid_expenses = fields.Boolean(string='Prepaid Expenses      | 3rd Business Day')
    is_third_party_borrowing = fields.Boolean(string='Third Party Borrowing | 2nd Business Day')
    is_aro = fields.Boolean(string='ARO | -1 Business Day')

    is_depreciation_schedules = fields.Boolean(string='Depreciation Schedules (Please insert Description box below) | 2nd Business Day')
    depreciation_schedules = fields.Char(string='Depreciation Schedules Description | 2nd Business Day')
    is_net_assets_schedules = fields.Boolean(string='Net Assets Schedules | 15th Business Day')
    is_intangible_assets_schedules = fields.Boolean(string='Intangible Assets Schedules | 2nd Business Day')
    is_intercompany_ar_ap_schedule = fields.Boolean(string='Intercompany A/R & A/P Schedules (Please insert Description box below) | 10th Business Day')
    intercompany_ar_ap_schedule = fields.Char(string='Intercompany A/R & A/P Schedules Description | 10th Business Day')
    is_cash_reconcile = fields.Boolean(string='Cash Reconciliation (Please insert Description box below) | 3rd Business Day')
    cash_reconcile = fields.Char(string='Cash Reconciliation Description | 3rd Business Day')

    description = fields.Html(string='Description')


    @api.constrains('date_of_project', 'resource_user_id')
    def _check_unique_date_and_user(self):
        """Ensure that no two records have the same date_of_project and resource_user_id."""
        for record in self:
            existing_record = self.env['daily.progress.business'].search([
                ('date_of_project', '=', record.date_of_project),
                ('resource_user_id', '=', record.resource_user_id.id),
                ('id', '!=', record.id)  # Exclude the current record in case of update
            ])
            if existing_record:
                raise ValidationError(
                    "A record with the same 'Today Date' and 'Resource Name' already exists. You cannot create duplicate records for the same user on the same date.")

    @api.onchange('date_of_project')
    def onchange_date_of_project(self):
        for rec in self:
            if rec.date_of_project and rec.date_of_project > date.today():
                raise UserError("The date of the project cannot be in the future. Please select a valid date.")

    @api.depends('date_of_project')
    def _compute_week_of_year(self):
        """Compute week number (ISO week) based on date_of_project."""
        for record in self:
            if record.date_of_project:
                # ISO week number (1–53, starting Monday)
                iso_year, week_number, _ = record.date_of_project.isocalendar()
                record.week_of_year = f"Week-{week_number}"
                record.year_of_kpi = iso_year
            else:
                record.week_of_year = ""
                record.year_of_kpi = ""
