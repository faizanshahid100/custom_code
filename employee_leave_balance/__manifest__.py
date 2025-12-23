{
    "name": "Employee Leave Balance Report",
    "version": "1.0",
    "category": "Human Resources",
    "summary": "View allocated, used, and remaining leaves per employee",
    "depends": ["hr", "hr_holidays"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_crones.xml",
        "views/employee_leave_summary.xml",
    ],
    "installable": True,
    "application": False,
}
