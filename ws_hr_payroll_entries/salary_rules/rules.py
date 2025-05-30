##################OVERTIME OLD########################################
date_from = str(payslip.date_from)
year = int(date_from[:4])  # Extract year
month = int(date_from[-5:-3])  # Extract month

# Determine the number of days in the month, including leap year handling for February
if month in {1, 3, 5, 7, 8, 10, 12}:
    days = 31
elif month == 2:
    days = 29 if (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)) else 28
else:
    days = 30

# Fetch approved overtime records for the employee in the payslip period
overtime_requests = payslip.env['approval.request'].search([
    ('category_id.sequence_code', '=', 'OVERTIME'),
    ('request_owner_id', '=', employee.user_id.id),
    ('date_start', '>=', payslip.date_from),
    ('date_end', '<=', payslip.date_to),
    ('request_status', '=', 'approved')
])

# Initialize total overtime pay
total_overtime_pay = 0

# Get Gross Salary from Payslip (Assuming categories.BASIC and categories.ALW exist)
gross_salary = (categories.BASIC or 0) + (categories.ALW or 0)

# Avoid division by zero errors
per_day_salary = gross_salary / days if gross_salary else 0
per_hour_salary = per_day_salary / 8 if per_day_salary else 0

for att in overtime_requests:
    hours = (att.date_end - att.date_start).total_seconds() / 3600  # Convert to hours

    if att.overtime_type == 'working_day':
        rate_multiplier = 2  # Double pay for working days
        total_overtime_pay += hours * (per_hour_salary * rate_multiplier)

    elif att.overtime_type == 'holiday':
        # First 8 hours at standard rate, additional hours at double rate
        standard_hours = min(hours, 8)
        extra_hours = max(0, hours - 8)

        total_overtime_pay += (standard_hours * per_hour_salary) + (extra_hours * (per_hour_salary * 2))

result = total_overtime_pay  # Final calculated overtime pay
################### OVERTIME ####################################
date_from = str(payslip.date_from)
year = int(date_from[:4])  # Extract year
month = int(date_from[-5:-3])  # Extract month

# Determine the number of days in the month, including leap year handling for February
days = 31 if month in {1, 3, 5, 7, 8, 10, 12} else 30 if month != 2 else (29 if (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)) else 28)

# Fetch approved overtime records for the employee in the payslip period
overtime_requests = payslip.env['approval.request'].search([
    ('category_id.sequence_code', '=', 'OVERTIME'),
    ('request_owner_id', '=', employee.user_id.id),
    ('date_start', '>=', payslip.date_from),
    ('date_end', '<=', payslip.date_to),
    ('request_status', '=', 'approved')
])

# Initialize total overtime pay
total_overtime_pay = 0

# Get Gross Salary from Payslip (Assuming categories.BASIC and categories.ALW exist)
gross_salary = (categories.BASIC or 0) + (categories.ALW or 0)

# Avoid division by zero errors
per_day_salary = gross_salary / days if gross_salary else 0
per_hour_salary = per_day_salary / 8 if per_day_salary else 0

for att in overtime_requests:
    hours = (att.date_end - att.date_start).total_seconds() / 3600  # Convert to hours
    total_overtime_pay += hours * (per_hour_salary * 3)  # Always 3x pay rate for overtime

result = total_overtime_pay  # Final calculated overtime pay

#################### Absent Deduction #########################
date_from = str(payslip.date_from)
year = int(date_from[:4])  # Extract year
month = int(date_from[-5:-3])  # Extract month

# Determine the number of days in the month, including leap year handling for February
# if month in {1, 3, 5, 7, 8, 10, 12}:
#     days = 31
# elif month == 2:
#     days = 29 if (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)) else 28
# else:
#     days = 30
days = 30
# Calculate contract-based allowances
contract_basic = contract.wage + contract.travel_allowances + contract.fuel_allowances + contract.relocation_allowances
per_day = contract_basic / days  # Daily rate calculation

absent_days = 0

# Loop through worked days and check for both "Out of Contract" and "Unpaid Time Off"
for rec in payslip.worked_days_line_ids:
    if rec.work_entry_type_id.name in ["Out of Contract", "Unpaid Time Off"]:
        absent_days += rec.number_of_days  # Add days for both types

result = per_day * absent_days