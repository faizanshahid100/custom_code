{
    "name": "Employee Leave Balance Report",
    "version": "1.0",
    "category": "Human Resources",
    "summary": "View allocated, used, and remaining leaves per employee",
    "depends": ["hr", "hr_holidays"],
    "data": [
        "security/ir.model.access.csv",
        "views/employee_leave_summary.xml",
        "wizards/leave_summary_wizard.xml",
    ],
    "installable": True,
    "application": False,
}
