from flask import Flask, redirect, url_for, session
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.vouchers import vouchers_bp
from routes.reports import reports_bp
from routes.chart import chart_bp
from models import reload_vouchers
from database import init_db
init_db()  # Tables create ho jayenge

app = Flask(__name__)
app.secret_key = 'skylume_erp_super_secret_key_2025_change_this_please'  # Strong key rakho

# Register Blueprints
app.register_blueprint(auth_bp)  # Login/Logout (no prefix)
app.register_blueprint(dashboard_bp)  # Dashboard
app.register_blueprint(vouchers_bp, url_prefix='/vouchers')
app.register_blueprint(reports_bp, url_prefix='/reports')
app.register_blueprint(chart_bp, url_prefix='/chart')

# App startup pe data load karo (Flask 3.0+ ke liye sahi tarika)
with app.app_context():
    reload_vouchers()

# Home route - root URL
@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('dashboard.dashboard'))
    return redirect(url_for('auth.login'))

# Custom 404 page
@app.errorhandler(404)
def page_not_found(e):
    return '''
    <div style="text-align:center; margin-top:100px;">
        <h1>404 - Page Not Found</h1>
        <p>Sorry, the page you are looking for does not exist.</p>
        <a href="{{ url_for('dashboard.dashboard') }}">Go to Dashboard</a>
    </div>
    ''', 404

# Custom 500 page
@app.errorhandler(500)
def internal_error(e):
    return '''
    <div style="text-align:center; margin-top:100px;">
        <h1>500 - Internal Server Error</h1>
        <p>Something went wrong on our end. Please try again later.</p>
    </div>
    ''', 500

if __name__ == '__main__':
    app.run(debug=True)