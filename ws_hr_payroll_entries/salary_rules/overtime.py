##################OVERTIME########################################
date_from = str(payslip.date_from)
month = int(date_from[-5:-3])
if month == 1 or month == 3 or month == 5 or month == 7 or month == 8 or month == 10 or month == 12:
    days = 31
elif month == 2:
    days = 28
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

# Ensure we have valid overtime records before processing
if overtime_requests:
    total_overtime_pay = 0  # Initialize total overtime pay

    # Get Gross Salary from Payslip (Assuming categories.BASIC and categories.ALW exist)
    gross_salary = categories.BASIC + categories.ALW if categories.BASIC and categories.ALW else 0

    # Avoid division by zero errors
    per_day_salary = gross_salary / days if gross_salary else 0  # Assuming 30-day month
    per_hour_salary = per_day_salary / 8 if per_day_salary else 0  # Assuming 8-hour workday

    for att in overtime_requests:
        hours = (att.date_end - att.date_start).total_seconds() / 3600  # Convert to hours

        # Determine pay rate based on overtime type
        if att.overtime_type == 'working_day':
            rate_multiplier = 2  # Double pay for working days
        elif att.overtime_type == 'holiday':
            rate_multiplier = 1  # Standard pay for holidays
        else:
            rate_multiplier = 0  # If no valid type, no payment

        # Accumulate total overtime pay
        total_overtime_pay += hours * (per_hour_salary * rate_multiplier)

    result = total_overtime_pay  # Final calculated overtime pay
else:
    result = 0  # No overtime, no extra pay
