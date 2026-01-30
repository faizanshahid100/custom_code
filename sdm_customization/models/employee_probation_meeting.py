from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import date


class EmployeeProbationMeeting(models.Model):
    _name = "employee.probation.meeting"
    _description = "Employee Probation Meeting"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "employee_id"

    employee_id = fields.Many2one("hr.employee", string="Employee Name", required=True)
    department_id = fields.Many2one(
        "hr.department",
        string="Department",
        compute="_compute_department_id",
        store=True,
    )
    employee_joining_date = fields.Date(related="employee_id.joining_date", string="Joining Date", store=True)
    employee_probation_end_date = fields.Date(related="employee_id.confirmation_date", string="Probation End Date",
                                              store=True)
    state = fields.Selection([
        ('inprogress', 'In Progress'),
        ('completed', 'Completed'),
    ], string='Status', default='completed', tracking=True)
    date_meeting = fields.Date(string="Meeting Date", default=lambda self: date.today(), required=True)
    probation_type = fields.Selection([
        ("pre", "Pre-Probation"),
        ("post", "Post-Probation"),
    ], string="Probation Type", required=True)

    probation_time = fields.Selection([
        ("0_1", "Less Than a Month"),
        ("1_3", "Month 1-3"),
        ("3_6", "Month 3-6"),
        ("6_onwards", "Month 6-Onwards"),
    ], string="Probation Time", required=True)

    meeting_status = fields.Selection([
        ("green", "Green"),
        ("yellow", "Yellow"),
        ("red", "Red"),
        ("blue", "Blue"),
    ], string="Employee Status", required=True, tracking=True)
    department_master_ids = fields.Many2many('department.master', string='Assign Department')

    reason = fields.Text(string="Reason (If Yellow/Red)", help="Specify reason for concern if status is not Green",
                         tracking=True)
    task_assign_line_ids = fields.One2many(
        "task.assign.lines",
        "meeting_id",
        string="Task Assignment Lines"
    )

    assignee_id = fields.Many2one('hr.employee', string='Task Assign To', tracking=True)
    employee_pulse_id = fields.Many2one('employee.pulse.profile', string='Employee Pulse')

    # Pre-Probation Questions
    q1_rating = fields.Selection([
        ('satisfied', 'Satisfied'),
        ('neutral', 'Neutral'),
        ('not_satisfied', 'Not Satisfied'),
    ], string="1. How is your experience going so far?")
    q1_experience = fields.Char(string="Q1 Explanation")
    #
    q2_rating = fields.Selection([
        ('satisfied', 'Satisfied'),
        ('neutral', 'Neutral'),
        ('not_satisfied', 'Not Satisfied'),
    ], string="2. Are you aligned with the client?")
    q2_alignment = fields.Char(string="Q2 Explanation")

    q3_rating = fields.Selection([
        ('satisfied', 'Satisfied'),
        ('neutral', 'Neutral'),
        ('not_satisfied', 'Not Satisfied'),
    ], string="3. Filling attendance in Odoo and KPI?")
    q3_attendance_kpi = fields.Char(string="Q3 Explanation")

    q4_rating = fields.Selection([
        ('satisfied', 'Satisfied'),
        ('neutral', 'Neutral'),
        ('not_satisfied', 'Not Satisfied'),
    ], string="4. Getting guidance from the client?")
    q4_guidance = fields.Char(string="Q4 Explanation")

    q5_rating = fields.Selection([
        ('satisfied', 'Satisfied'),
        ('neutral', 'Neutral'),
        ('not_satisfied', 'Not Satisfied'),
    ], string="5. Using Hubstaff?")
    q5_hubstaff = fields.Char(string="Q5 Explanation")

    q6_rating = fields.Selection([
        ('satisfied', 'Satisfied'),
        ('neutral', 'Neutral'),
        ('not_satisfied', 'Not Satisfied'),
    ], string="6. Any challenges?")
    q6_challenges = fields.Char(string="Q6 Explanation")

    q7_rating = fields.Selection([
        ('satisfied', 'Satisfied'),
        ('neutral', 'Neutral'),
        ('not_satisfied', 'Not Satisfied'),
    ], string="7. What's your daily tasks and how many team members you have?")
    q7_daily_tasks = fields.Char(string="Q7 Explanation")

    # Post-Probation Question
    q1_rating_post = fields.Selection([
        ('good', 'Good'),
        ('average', 'Average'),
        ('poor', 'Poor'),
    ], string="1. How are things going overall with Prime?")
    q1_experience_post = fields.Char(string="Q1 Explanation")

    q2_rating_post = fields.Selection([
        ('excellent', 'Excellent'),
        ('satisfactory', 'Satisfactory'),
        ('needs_improvement', 'Needs Improvement'),
    ], string="2. How is your work progress and experience on the client side?")
    q2_experience_post = fields.Char(string="Q2 Explanation")

    q3_rating_post = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string="3. Have you faced any challenges recently that may be affecting your performance or work quality?")
    q3_experience_post = fields.Char(string="Q3 Explanation")

    q4_rating_post = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ],
        string="4. Are you experiencing any issues with your system, laptop, or headgear that require attention from the IT team?")
    q4_experience_post = fields.Char(string="Q4 Explanation")

    q5_rating_post = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ],
        string="5. Do you have any concerns, queries, or feedback that you would like to share regarding your role or responsibilities?")
    q5_experience_post = fields.Char(string="Q5 Explanation")

    selected_employee_ids = fields.Many2many(
        "hr.employee",
        "employee_meeting_mail_rel",
        "meeting_id",
        "employee_id",
        string="CC Mail To",
        help="Select employees who will receive the reason email if meeting status is Red or Yellow."
    )
    is_audit = fields.Boolean('Is Audit', default=False)
    comment = fields.Text('Overall Comments')

    is_mail_sent = fields.Boolean(string="Mail Sent", tracking=True)

    action_taken_comment = fields.Char(string='Action Taken', tracking=True)
    action_employee_ids = fields.Many2many(
        "hr.employee",
        "employee_meeting_action_mail_rel",
        "meeting_id",
        "employee_id",
        string="Send Action Mail To",
        help="Employees who will receive the action taken update email."
    )
    is_action_mail_sent = fields.Boolean(string="Action Mail Sent", readonly=True, tracking=True)

    # Month 0-1
    overall_experience = fields.Text(
        string="How has your overall experience been this week while working with the client and Prime?"
    )

    challenges_obstacles = fields.Text(
        string="Are you facing any challenges or obstacles in your role (workload, processes, communication, or tools)?"
    )

    support_feedback = fields.Text(
        string="Do you feel you are getting the support you need from the client team and Prime management? If not, what could be improved?"
    )

    motivation_engagement = fields.Text(
        string="Is there anything affecting your motivation, engagement, or job satisfaction that you’d like to share?"
    )

    concerns_suggestions = fields.Text(
        string="Do you have any concerns, suggestions, or issues you would like us to address or escalate on your behalf?"
    )


    # Month 1-3
    # Setting In & Adjustment
    settling_with_team = fields.Text(string='How are you settling into the role and team?')
    time_zone_schedule = fields.Text(string='How is the time zone / schedule working for you?')
    fatigue_sustainability_concerns = fields.Text(string='Any fatigue or sustainability concerns?')
    # Tools & Equipment
    equipment_system_access = fields.Text(string='Do you have all the equipment and system access you need?')
    technical_setup_issues = fields.Text(string='Any technical or setup issues slowing you down?')
    # Role Clarity
    # Do you feel clear on
    day_to_day_responsibilities = fields.Text(string='Day-to-day responsibilities?')
    priorities_expectations = fields.Text(string='Priorities and expectations?')
    gray_areas_assumptions = fields.Text(string='Any gray areas or assumptions that need clarification?')
    # Manager Connection
    regular_scheduled_manager = fields.Text(string='Are regular 1:1s scheduled with your manager?')
    comfortable_raising_concerns = fields.Text(string='Do you feel comfortable raising questions or concerns?')
    # Early Support Needs
    team_help_needed = fields.Text(string='Anything Prime or the client team can do to help you ramp faster?')

    # Month 3-6
    # Self-Assessment
    personally_gauge_performance = fields.Text(string='How do you personally gauge your performance so far?')
    fell_really_well = fields.Text(string='What do you feel you’re doing really well?')
    you_could_improve = fields.Text(string='Where do you think you could improve?')
    # Client Feedback Transparency
    set_expectations = fields.Text(string='Set expectations - prime will be getting feedback from your manager.')
    # Manager Alignment
    feedback_received = fields.Text(string='What feedback have you received so far?')
    expectations_consistent_clear = fields.Text(string='Are expectations consistent and clear?')
    surprises_misalignments = fields.Text(string='Any surprises or misalignments?')
    # Growth & Capability
    challenged_enough = fields.Text(string='Are you being challenged enough?')
    skills_exposure_want = fields.Text(string='Any skills you’d like to build or exposure you want?')
    # Engagement & Motivation
    motivated_in_role = fields.Text(string='What keeps you motivated in this role?')
    morale_confidence = fields.Text(string='Anything impacting morale or confidence?')

    # Month 6-Onwards
    # Contribution & Impact
    proud_contributions = fields.Text(string='What contributions are you most proud of?')
    adding_values = fields.Text(string='Where do you feel you’re adding the most value?')
    # Value Add Beyond the Role
    improvements_ideas_initiatives = fields.Text(string='Any process improvements, ideas, or initiatives you’ve contributed?')
    make_an_impact = fields.Text(string='Where else could you make an impact?')
    # Recognition & Shout-Outs
    wins_shout_outs_by_client = fields.Text(string='Any wins or shout-outs from the client team?')
    acknowledge_document_successes = fields.Text(string='Acknowledge and document successes.')
    # Career & Progression
    role_evolving = fields.Text(string='How do you see your role evolving?')
    interest_in = fields.Selection([('responsibility', 'Higher responsibility?'),
                                    ('mentorship', 'Mentorship?'), ('scope', 'Expanded scope?')], string='Interest in:')
    # Long-Term Alignment
    what_success_look_like = fields.Text(string='What would “success” look like for you over the next 12 months?')


    def action_resolve(self):
        """Mark record as Completed"""
        self.write({'state': 'completed'})

    # def action_set_inprogress(self):
    #     """Revert to In Progress"""
    #     self.write({'state': 'inprogress'})

    @api.depends("employee_id", "employee_id.department_id")
    def _compute_department_id(self):
        """Automatically fetch the department of the selected employee."""
        for record in self:
            record.department_id = record.employee_id.department_id.id if record.employee_id else False

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        """Update related fields and probation type when employee changes"""
        today = date.today()
        for rec in self:
            employee = rec.employee_id
            if not employee:
                rec.employee_pulse_id = False
                rec.probation_type = False
                rec.probation_time = False
                return

            # Set pulse profile
            rec.employee_pulse_id = employee.employee_pulse_id.id if employee.employee_pulse_id else False

            # Validate confirmation date
            if not employee.confirmation_date:
                raise ValidationError(
                    _("Confirmation date for %s is not mentioned in the Employee form.") % employee.name)

            # Determine probation type
            rec.probation_type = 'pre' if today < employee.confirmation_date else 'post'

            # -------------------------------
            # Determine probation time
            # -------------------------------
            if not employee.joining_date:
                rec.probation_time = False
                return

            months_diff = (
                    (today.year - employee.joining_date.year) * 12
                    + (today.month - employee.joining_date.month)
            )

            if months_diff <= 1:
                rec.probation_time = '0_1'
            elif 1 < months_diff <= 3:
                rec.probation_time = '1_3'
            elif 3 < months_diff <= 6:
                rec.probation_time = '3_6'
            else:
                rec.probation_time = '6_onwards'

    @api.onchange('task_assign_line_ids')
    def _onchange_task_assign_line_ids(self):
        if all(self.task_assign_line_ids.mapped('sdm_task_confirmed')):
            self.state = 'completed'
        else:
            self.state = 'inprogress'

    # ----------------------------
    # Send Reason Mail
    # ----------------------------
    def action_send_reason_mail(self):
        # TODO (Inprogress)
        """Send email with reason, employee name, date, and record link to assignee (To:) and selected employees (CC:)"""
        for record in self.task_assign_line_ids.filtered(lambda l: not l.sdm_task_confirmed):
            if not record.reason:
                raise UserError("Please mention a reason before sending the email.")
            if not record.to_employee_ids or not any(emp.work_email for emp in record.to_employee_ids):
                raise UserError("Please assign an employee (with a work email) as the task assignee.")

            # Get base URL for record link
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            record_url = f"{base_url}/web#id={self.id}&model=employee.probation.meeting&view_type=form"

            # Email subject and body
            subject = f"Probation Meeting Update for {self.employee_id.name}"
            body = f"""
                <div style="font-family:Arial, sans-serif; line-height:1.6;">
                    <h3 style="color:#004080;">Probation Meeting Summary</h3>
                    <p>Hi <b>{", ".join(record.to_employee_ids.mapped("name"))}</b>,</p>
                    <p>You have been assigned the following probation review task:</p>
                    <p><b>Employee:</b> {self.employee_id.name}</p>
                    <p><b>Meeting Date:</b> {self.date_meeting.strftime('%d-%m-%Y')}</p>
                    <p><b>Probation Time:</b> {self.probation_time.replace('_', '- probation_time').title()} Months Probation</p>
                    <p><b>Reason:</b> {record.reason}</p>
                    <p><b>Priority:</b> {'⭐' * int(record.priority)}</p>
                    <p>You can view the full meeting record here:
                        <a href="{record_url}" target="_blank">View in Odoo</a>
                    </p>
                    <br/>
                    <p style="color:#666;">--<br/>Sent automatically from Odoo HR System</p>
                </div>
            """

            # Build CC list from selected employees
            to_emails = [emp.work_email for emp in record.to_employee_ids if emp.work_email]
            cc_emails = [emp.work_email for emp in record.cc_employee_ids if emp.work_email]

            # # Add default CC for users in the "Managers" security group
            # manager_group = self.env.ref('prime_sol_custom.prime_group_managers', raise_if_not_found=False)
            # if manager_group:
            #     manager_users = manager_group.users.filtered(lambda u: u.partner_id.email)
            #     cc_emails.extend([u.partner_id.email for u in manager_users])

            # Remove duplicates and join into comma-separated string
            to_emails = ','.join(set(to_emails))
            cc_emails = ','.join(set(cc_emails))

            # Prepare mail
            mail_values = {
                'subject': subject,
                'body_html': body,
                'email_from': 'sdm@primesystemsolutions.com',
                'email_to': to_emails,
                'email_cc': cc_emails,
            }

            # Send email
            self.env['mail.mail'].sudo().create(mail_values).send()
        self.is_mail_sent = True

class TaskAssignLines(models.Model):
    _name = "task.assign.lines"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Task Assignment Lines"

    meeting_id = fields.Many2one(
        "employee.probation.meeting",
        string="Probation Meeting",
        ondelete="cascade"
    )


    reason = fields.Text('Reason Details', tracking=True)
    action_taken_comment = fields.Text('Action Taken', tracking=True)
    to_employee_ids = fields.Many2many(
        "hr.employee",
        "task_assign_to_rel",
        "task_id",
        "employee_id",
        help='Only SDM Group member can see this',
        string="To", tracking=True
    )

    cc_employee_ids = fields.Many2many(
        "hr.employee",
        "task_assign_cc_rel",
        "task_id",
        "employee_id",
        help='Only SDM Group member can see this',
        string="CC", tracking=True
    )
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Medium'),
        ('2', 'High'),
        ('3', 'Very High'),
    ], string="Task Priority", default='1')

    assign_date = fields.Date('Assign date', default=lambda self: date.today(), tracking=True)
    employee_task_confirmed = fields.Boolean(string="Employee Confirmed", tracking=True)
    sdm_task_confirmed = fields.Boolean(string="SDM Confirmed", help='Only SDM Group member can see this', tracking=True)

    confirmed_date = fields.Date(string="Confirmation Date", default=fields.Date.today, tracking=True)

    @api.onchange('sdm_task_confirmed')
    def _onchange_sdm_task_confirmed(self):
        for rec in self:
            if rec.sdm_task_confirmed:
                rec.confirmed_date = fields.Date.today()

    def action_send_action_mail(self):
        for record in self:
            if not record.employee_task_confirmed:
                raise UserError("Please mark 'Employee Confirmed' before sending the email.")

            if not record.meeting_id:
                raise UserError("No meeting linked with this task line.")

            # ✅ Safe to generate real record URL now
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            record_url = f"{base_url}/web#id={record.meeting_id.id}&model=employee.probation.meeting&view_type=form"

            subject = f"Action Taken Update for {record.meeting_id.employee_id.name}'s Probation Meeting"
            body = f"""
                <div style="font-family:Arial, sans-serif; line-height:1.6;">
                    <h3 style="color:#004080;">Probation Meeting Action Update</h3>
                    <p><b>Task Completed:</b> ✅</p>
                    <p><b>Employee:</b> {record.meeting_id.employee_id.name}</p>
                    <p><b>Date:</b> {record.meeting_id.date_meeting.strftime('%d-%m-%Y')}</p>
                    <p><b>Action Taken:</b> {record.action_taken_comment or 'Resolved'}</p>
                    <p>You can view this meeting record in Odoo:
                        <a href="{record_url}" target="_blank">View Record</a>
                    </p>
                </div>
            """

            # Manager group
            manager_group = self.env.ref('prime_sol_custom.prime_group_managers', raise_if_not_found=False)
            if not manager_group:
                raise UserError("Manager group not found: prime_sol_custom.prime_group_managers")

            manager_emails = [u.partner_id.email for u in manager_group.users if u.partner_id.email]
            if not manager_emails:
                raise UserError("No manager emails found in the manager group.")

            to_emails = ','.join(set(manager_emails))

            # ✅ Send email safely after record is saved
            self.env['mail.mail'].sudo().create({
                'subject': subject,
                'body_html': body,
                'email_from': 'sdm@primesystemsolutions.com',
                'email_to': to_emails,
            }).send()

            record.confirmed_date = fields.Date.today()

        return True

