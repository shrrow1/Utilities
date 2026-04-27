from flask import Flask, render_template, request
from datetime import datetime, timedelta

app = Flask(__name__)

# UK Bank Holidays 2024-2026
BANK_HOLIDAYS = [
    # 2024
    '2024-01-01', '2024-03-29', '2024-04-01', '2024-05-06', '2024-05-27', '2024-08-26', '2024-12-25', '2024-12-26',
    # 2025
    '2025-01-01', '2025-04-18', '2025-04-21', '2025-05-05', '2025-05-26', '2025-08-25', '2025-12-25', '2025-12-26',
    # 2026
    '2026-01-01', '2026-04-03', '2026-04-06', '2026-05-04', '2026-05-25', '2026-08-31', '2026-12-25', '2026-12-26'
]

def get_working_days(start_date, end_date):
    working_days = 0
    current_date = start_date
    while current_date < end_date:
        # Check if weekday (0-4 is Mon-Fri) and not a bank holiday
        if current_date.weekday() < 5 and current_date.strftime('%Y-%m-%d') not in BANK_HOLIDAYS:
            working_days += 1
        current_date += timedelta(days=1)
    return working_days

@app.route('/')
def index():
    target_date = datetime(2026, 12, 24)
    
    date_override = request.args.get('date')
    if date_override:
        try:
            now = datetime.strptime(date_override, '%Y-%m-%d')
        except ValueError:
            now = datetime.now()
    else:
        now = datetime.now()

    delta = target_date - now
    days_remaining = max(0, delta.days + (1 if delta.seconds > 0 or delta.microseconds > 0 else 0))
    
    # Calculate working days
    work_days = get_working_days(now, target_date)
    
    # Check for 'holidays' override in URL params (default: 44)
    try:
        holiday_count = int(request.args.get('holidays', 44))
    except (ValueError, TypeError):
        holiday_count = 44
    
    # 3rd Screen Logic: Working days - holiday_count
    holiday_calc = max(0, work_days - holiday_count)
    
    print(f"DEBUG: Days: {days_remaining} | Work: {work_days} | Hols Subtracted: {holiday_count} | Calc: {holiday_calc}", flush=True)
    
    return render_template('index.html', days=days_remaining, work_days=work_days, holiday_calc=holiday_calc)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
