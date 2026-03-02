from odoo import models, fields


class CeoMeeting(models.Model):
    _name = 'ceo.meeting'
    _description = 'CEO Meeting Management'
    _rec_name = 'employee_id'
    _order = 'create_date desc'

    # ─────────────────────────────────────────────────────────────────────
    # Section 1: Basic Profile
    # ─────────────────────────────────────────────────────────────────────
    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Employee Name',
        required=True,
        ondelete='cascade',
    )
    designation = fields.Many2one(
        comodel_name='hr.job',
        string='Designation',
        related='employee_id.job_id',
        store=True,
        readonly=True,
    )
    client_id = fields.Many2one(
        comodel_name='res.partner',
        string='Client',
        related='employee_id.contractor',
        store=True,
        readonly=True,
    )
    reporting_manager_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Reporting Manager',
        related='employee_id.parent_id',
        store=True,
        readonly=True,
    )
    working_since = fields.Date(
        string='Working Since',
        related='employee_id.joining_date',
        store=True,
        readonly=True,
    )

    # ─────────────────────────────────────────────────────────────────────
    # Section 2: Current Engagement
    # ─────────────────────────────────────────────────────────────────────
    project_role_ids = fields.Many2many(
        comodel_name='ceo.project.role',
        relation='ceo_meeting_project_role_rel',
        column1='meeting_id',
        column2='role_id',
        string='Current Project Role',
    )
    scope_of_work_ids = fields.Many2many(
        comodel_name='ceo.scope.work',
        relation='ceo_meeting_scope_work_rel',
        column1='meeting_id',
        column2='scope_id',
        string='Scope of Work',
    )
    kpi_deliverable_ids = fields.Many2many(
        comodel_name='ceo.kpi.deliverable',
        relation='ceo_meeting_kpi_deliverable_rel',
        column1='meeting_id',
        column2='kpi_id',
        string='KPIs Deliverable',
    )
    kadence_ids = fields.Many2many(
        comodel_name='ceo.kadence',
        relation='ceo_meeting_kadence_rel',
        column1='meeting_id',
        column2='kadence_id',
        string='Kadence',
    )

    # ─────────────────────────────────────────────────────────────────────
    # Section 3: Performance Snapshot
    # ─────────────────────────────────────────────────────────────────────
    last_performance_rating = fields.Selection(
        selection=[
            ('1', '1 - Poor'),
            ('2', '2 - Below Average'),
            ('3', '3 - Average'),
            ('4', '4 - Good'),
            ('5', '5 - Excellent'),
        ],
        string='Last Performance Rating',
    )
    last_escalation = fields.Text(
        string='Last Escalation (If Any)',
    )
    last_feedback = fields.Char(
        string='Last Feedback',
    )
    last_achievement = fields.Selection(
        selection=[
            ('30days', 'Last 30 Days'),
            ('60days', 'Last 60 Days'),
        ],
        string='Last Achievement',
    )
    last_achievement_detail = fields.Text(
        string='Achievement Detail',
    )

    # ─────────────────────────────────────────────────────────────────────
    # Section 4: Touch Points History
    # ─────────────────────────────────────────────────────────────────────
    last_ceo_interaction_date = fields.Date(
        string='Last CEO Interaction Date',
    )
    last_ceo_interaction_summary = fields.Text(
        string='CEO Interaction Summary',
    )
    last_client_interaction_date = fields.Date(
        string='Last Client Interaction Date',
    )
    last_client_interaction_summary = fields.Text(
        string='Client Interaction Summary',
    )
    internal_review_meeting = fields.Text(
        string='Internal Review Meeting',
    )

    # ─────────────────────────────────────────────────────────────────────
    # Section 5: Risk & Flags
    # ─────────────────────────────────────────────────────────────────────
    retention_risk = fields.Selection(
        selection=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
        ],
        string='Retention Risk',
    )
    performance_risk = fields.Selection(
        selection=[
            ('positive', 'Positive'),
            ('negative', 'Negative'),
            ('neutral', 'Neutral'),
            ('positive_neutral', 'Positive Neutral'),
            ('negative_neutral', 'Negative Neutral'),
        ],
        string='Performance Risk',
    )
    client_satisfaction_status = fields.Selection(
        selection=[
            ('green', 'Green'),
            ('yellow', 'Yellow'),
            ('red', 'Red'),
        ],
        string='Client Satisfaction Status',
    )

    # ─────────────────────────────────────────────────────────────────────
    # Section 6: Meeting Objective
    # ─────────────────────────────────────────────────────────────────────
    purpose_of_meeting = fields.Text(
        string='Purpose of Meeting',
    )
    expected_outcome = fields.Text(
        string='Expected Outcome',
    )
    key_questions_for_ceo = fields.Text(
        string='Key Questions for CEO',
    )
    next_meeting_appointment = fields.Datetime(
        string='Next Meeting Appointment',
    )
