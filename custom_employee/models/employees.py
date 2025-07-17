# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging
from datetime import date, timedelta

_logger = logging.getLogger(__name__)


class HREmployeeInherit(models.Model):
    _inherit = 'hr.employee'

    employee_status = fields.Selection([('active', 'Active'),
                                        ('passive', 'Passive')],
                                       string='Employee Status', default='active', tracking=True)
    blood_group = fields.Selection([('a+', 'A+'), ('a-', 'A-'), ('b+', 'B+'), ('b-', 'B-'), ('o+', 'O+'), ('o-', 'O-'),
                                    ('ab-', 'AB-'), ('ab+', 'AB+')],
                                   string='Blood Group', tracking=True)
    cnic_expiry = fields.Date(string="Identification Expiry")
    citizenship_id = fields.Char(string="Citizenship ID")
    province = fields.Char(string='Province')
    chronic_diseases = fields.Selection([('yes', 'Yes'),
                                         ('no', 'No')],
                                        string='Chronic Diseases', tracking=True)
    meds_in_use = fields.Selection([('yes', 'Yes'),
                                    ('no', 'No')],
                                   string='Meds in Use', tracking=True)
    signed = fields.Char(string='Signed')
    joining_date = fields.Date(string='Joining Date')
    confirmation_date = fields.Date(string='Confirmation Date')
    leaving_date = fields.Date(string='Leaving Date')
    joining_salary = fields.Integer(string='Joining Salary')
    current_salary = fields.Integer(string='Current Salary')
    emergency_contact_relation = fields.Char(string="Relation")
    emp_father_name = fields.Char(string="Father Name")
    emp_father_cnic = fields.Char(string="Father CNIC")
    next_to_kin = fields.Char(string="Next to Kin")
    next_to_kin_relation = fields.Char(string="Next to Kin Relation")
    reference_check = fields.Char(string="Reference Check")
    background_check = fields.Char(string="Background Check")
    credit_check = fields.Char(string="Credit Check")
    working_country_id = fields.Many2one('res.country')
    job_type = fields.Selection([('full_time', 'Full-Time'), ('half_time', 'Half-Time')], string="Job Type",
                                default='full_time', required=True)
    is_probation = fields.Boolean('Is probation Period', default=True)
    notice_period = fields.Boolean(string="Under Notice Period", default=False)
    notice_period_date = fields.Date(string="Notice Period End Date")
    calendar_tracking_ids = fields.One2many('calendar.tracking', 'employee_id', string="Calendar Tracking")

    # Contract
    contractor = fields.Many2one('res.partner', string="Contractor", domain=[('is_company', '=', True)])
    contractor_email = fields.Char('Contractor Email')
    contractor_id = fields.Char(string="ID")
    business_unit = fields.Char(string="Business Unit")
    pl_code = fields.Char(string="PL Code")
    department = fields.Char(string="Dept")
    manager = fields.Char(string="Manager (Contractor)")
    manager_email = fields.Char(string="Manager Email")
    dept_hod = fields.Char(string="Dept HOD")
    dept_hod_email = fields.Char(string="Dept HOD Email")
    serving_region = fields.Char(string="Serving Region")
    shift_time = fields.Char(string="Shift Time")
    job_title = fields.Char(string="Job Time")
    level = fields.Char(string="Level")
    working_location = fields.Char(string="Working Location")
    rotation_based = fields.Char(string="Rotation Based")
    pss_group = fields.Selection([
        ('technical', 'Technical'),
        ('non_technical', 'Non-Technical'),
    ], string='PSS Group')
    emp_contract_type = fields.Char(string="Rotation Based")
    contract_start = fields.Date(string="Contract Start")
    client_joining_date = fields.Date(string="Joining Date Client")
    contract_end = fields.Date(string="Contract End")
    work_mode = fields.Selection([
        ('onsite', 'Onsite'),
        ('hybrid', 'Hybrid'),
        ('fully_remote', 'Fully Remote'),
    ], string='Work Mode')

    # Performance
    punctuality = fields.Integer(string="Punctuality")
    problem_solving = fields.Integer(string="Problem Solving")
    knowledge = fields.Integer(string="Knowledge")
    team_work = fields.Integer(string="Team Work")
    communication = fields.Integer(string="Communication")
    meet_kpi = fields.Integer(string="Meet Kpi's")
    avg_grande = fields.Integer(string="Avg Grade")
    month = fields.Integer(string="Month")

    # Employee Professional
    last_degree = fields.Char(string="Last Degree")
    year_of_grade = fields.Integer(string="Year of Grade")
    school_college_uni = fields.Char(string="School/College/Uni")
    hec_attested = fields.Boolean(string="HEC Attested")
    no_of_exp = fields.Integer(string="No of Exp")
    area_of_expertise = fields.Char(string="Area of Expertise")
    previous_company = fields.Char(string="Previous Company")

    # Health Insurance
    spouse_name = fields.Char(string="Spouse Name")
    spouse_cnic = fields.Char(string="Spouse CNIC")
    spouse_dob = fields.Date(string="Spouse DOB")
    child_name = fields.Char(string="Child Name")
    child_relation = fields.Char(string="Child Relation")
    child_dob = fields.Date(string="Child DOB")

    @api.model
    def create(self, vals):
        employee = super().create(vals)
        if vals.get('resource_calendar_id'):
            self.env['calendar.tracking'].create({
                'employee_id': employee.id,
                'resource_calendar_id': vals['resource_calendar_id'],
                'user_id': self.env.uid,
            })
        return employee

    def write(self, vals):
        res = super().write(vals)
        if 'resource_calendar_id' in vals:
            for employee in self:
                # Close previous tracking (if any)
                last_tracking = employee.calendar_tracking_ids.sorted(lambda r: r.start_date)[-1:]  # get last record
                if last_tracking and not last_tracking.end_date:
                    last_tracking.end_date = date.today() - timedelta(days=1)

                # Create new tracking
                self.env['calendar.tracking'].create({
                    'employee_id': employee.id,
                    'resource_calendar_id': vals['resource_calendar_id'],
                    'user_id': self.env.uid,
                })
        return res

    @api.model
    def update_dashboard_views_for_power_bi(self):
        """
        Drops and recreates the dashboard_employee_view and dashboard_employee_ticket_calls_view in PostgreSQL.
        This function is meant to be executed as a scheduled action.
        """
        query = """
            DROP VIEW IF EXISTS dashboard_employee_view;

            CREATE VIEW dashboard_employee_view AS
            SELECT
                e.id,
                e.name,
                e.active,
                e.joining_date,
                e.leaving_date,
                c.name AS country_name,  
                e.working_location,
                e.gender,
                rp.name AS contractor,
                e.serving_region,
                e.manager,
                d.name AS department_name,  
                j.name AS job_name,  
                e.job_type,
                e.notice_period,
                e.notice_period_date,
                e.birthday
            FROM
                hr_employee e
            LEFT JOIN
                res_country c ON e.working_country_id = c.id
            LEFT JOIN
                hr_department d ON e.department_id = d.id
            LEFT JOIN
                hr_job j ON e.job_id = j.id
            LEFT JOIN
                res_partner rp ON e.contractor = rp.id;

            DROP VIEW IF EXISTS dashboard_employee_ticket_calls_view;

            CREATE VIEW dashboard_employee_ticket_calls_view AS
            SELECT
                e.id AS employee_id,
                e.kpi_measurement,
                e.level,
                e.contractor,
                e.department_id,
                e.parent_id,
                e.employee_status,
                dp.date_of_project,
                dp.avg_resolved_ticket,
                dp.billable_hours,
                dp.non_billable_hours,
                dp.no_calls_duration,
                e.d_ticket_resolved,
                e.d_billable_hours,
                e.d_no_of_call_attended
            FROM
                hr_employee e
            LEFT JOIN
                res_users u ON e.user_id = u.id
            LEFT JOIN
                daily_progress dp ON dp.resource_user_id = u.id;
        """
        try:
            self.env.cr.execute(query)
            _logger.info("Successfully updated dashboard_employee_view and dashboard_employee_ticket_calls_view.")
        except Exception as e:
            _logger.error("Error updating views: %s", str(e))


class CalendarTracking(models.Model):
    _name = "calendar.tracking"
    _rec_name = "resource_calendar_id"
    _description = "Calendar Tracking"

    resource_calendar_id = fields.Many2one('resource.calendar', string="Working Schedule", required=True)
    user_id = fields.Many2one('res.users', string="User", required=True)
    start_date = fields.Date(string="Start Date", default=fields.Date.today(), required=True)
    end_date = fields.Date(string="End Date")
    employee_id = fields.Many2one('hr.employee', string="Employee", ondelete='cascade')
