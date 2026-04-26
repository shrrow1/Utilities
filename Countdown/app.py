from flask import Flask, render_template, request
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def index():
    print(f"DEBUG: Processing request for {request.url}", flush=True)
    target_date = datetime(2026, 12, 24)
    
    # Check for 'date' override in URL params (format: YYYY-MM-DD)
    date_override = request.args.get('date')
    if date_override:
        try:
            now = datetime.strptime(date_override, '%Y-%m-%d')
            print(f"DEBUG: Using date override: {now}", flush=True)
        except ValueError:
            print(f"DEBUG: Invalid date override format: {date_override}", flush=True)
            now = datetime.now()
    else:
        now = datetime.now()

    delta = target_date - now
    # Round up to show full days remaining
    days_remaining = max(0, delta.days + (1 if delta.seconds > 0 or delta.microseconds > 0 else 0))
    print(f"DEBUG: Target: {target_date} | Now: {now} | Result: {days_remaining} days", flush=True)
    
    return render_template('index.html', days=days_remaining)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
