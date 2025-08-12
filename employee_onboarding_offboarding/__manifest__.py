{
    "name": "Employee Onboarding/Offboarding",
    "version": "16.0.1.0.1",
    "license": "LGPL-3",
    "author": "Farooq Butt | Prime System Solutions",
    "website": "https://primesystemsolutions.com/",
    "summary": " ",
    "sequence": 1,
    "description": """""",
    "category": "HR Onboarding/Offboarding",
    "depends": [
        "hr", "hr_contract",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/security_groups.xml",
        "data/sequence.xml",
        "views/employee_onboard.xml",
        "views/checklist_requests.xml",
    ],
    "installable": True,
    "application": True,
}
