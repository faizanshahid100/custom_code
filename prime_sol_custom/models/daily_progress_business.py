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
        ('cas', 'Corporate Accounting Supervisor'),
        ('aps', 'Associate Procurement Specialist'),
        ('ps', 'Procurement Specialist'),
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
    yes_no_selection = [
        ('yes', 'Yes'),
        ('no', 'No'),
    ]

    is_accrued_expenses = fields.Selection(
        yes_no_selection, string='Accrued Expenses | 3rd Business Day', default='no'
    )
    is_decommissioning = fields.Selection(
        yes_no_selection, string='Decommissioning | -2 Business Day', default='no'
    )
    is_leases = fields.Selection(
        yes_no_selection, string='Leases | 1st Business Day', default='no'
    )
    is_other_current_assets = fields.Selection(
        yes_no_selection, string='Other Current Assets | 3rd Business Day', default='no'
    )
    is_prepaid_expenses = fields.Selection(
        yes_no_selection, string='Prepaid Expenses | 3rd Business Day', default='no'
    )
    is_third_party_borrowing = fields.Selection(
        yes_no_selection, string='Third Party Borrowing | 2nd Business Day', default='no'
    )
    is_aro = fields.Selection(
        yes_no_selection, string='ARO | -1 Business Day', default='no'
    )

    is_depreciation_schedules = fields.Selection(
        yes_no_selection, string='Depreciation Schedules | 2nd Business Day', default='no'
    )
    depreciation_schedules = fields.Char(
        string='Depreciation Schedules Description | 2nd Business Day'
    )
    is_net_assets_schedules = fields.Selection(
        yes_no_selection, string='Net Assets Schedules | 15th Business Day', default='no'
    )
    is_intangible_assets_schedules = fields.Selection(
        yes_no_selection, string='Intangible Assets Schedules | 2nd Business Day', default='no'
    )
    is_intercompany_ar_ap_schedule = fields.Selection(
        yes_no_selection, string='Intercompany A/R & A/P Schedules | 10th Business Day', default='no'
    )
    intercompany_ar_ap_schedule = fields.Char(
        string='Intercompany A/R & A/P Schedules Description | 10th Business Day'
    )
    is_cash_reconcile = fields.Selection(
        yes_no_selection, string='Cash Reconciliation | 3rd Business Day', default='no'
    )
    cash_reconcile = fields.Char(
        string='Cash Reconciliation Description | 3rd Business Day'
    )


    # Corporate Accounting Supervisor
    is_po_in_fom = fields.Selection(
        yes_no_selection, string='Update all the POs in FOM sheet', default='no'
    )
    is_je_in_netsuite = fields.Selection(
        yes_no_selection, string='Upload all the inventory JEs in Netsuite as per FOM sheet', default='no'
    )
    is_summary_sheet_of_je = fields.Selection(
        yes_no_selection, string='Update the summary sheet of JEs.', default='no'
    )
    is_preparation_inventory_reconciliation = fields.Selection(
        yes_no_selection, string='Preparation of on-site inventory reconciliation', default='no'
    )
    is_preparation_warehouse_reconciliation = fields.Selection(
        yes_no_selection, string='Preparation of warehouse inventory reconciliation', default='no'
    )

    # Associate Procurement Specialist and Procurement Specialist
    number_of_tickets = fields.Integer(string="Tickets assigned per week")
    number_of_opportunities = fields.Integer(string="Number of Opportunities per week")
    number_of_opportunities_won = fields.Integer(string="Number of Opportunities won per week")


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
