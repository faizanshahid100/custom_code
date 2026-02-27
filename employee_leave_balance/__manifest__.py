{
    "name": "Employee Leave Balance Report",
    "version": "1.0",
    "category": "Human Resources",
    "summary": "View allocated, used, and remaining leaves per employee",
    "license": "LGPL-3",
    "author": "Farooq Butt | Prime System Solutions",
    "website": "https://primesystemsolutions.com/",
    "depends": ["hr", "hr_holidays"],
    "data": [
        "security/ir.model.access.csv",
        "views/employee_leave_summary.xml",
        "wizards/leave_summary_wizard.xml",
    ],
    "installable": True,
    "application": False,
}
