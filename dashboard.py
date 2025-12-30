from flask import Blueprint, render_template, session, redirect, url_for
from models import bank_vouchers, cash_vouchers, journal_vouchers, sales_vouchers, purchase_vouchers
from datetime import datetime

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    
    # Voucher counts
    bank_count = len(bank_vouchers)
    cash_count = len(cash_vouchers)
    journal_count = len(journal_vouchers)
    sales_count = len(sales_vouchers)
    purchase_count = len(purchase_vouchers)
    
    total_vouchers = bank_count + cash_count + journal_count + sales_count + purchase_count
    
    # Current date for display
    now = datetime.now()

    return render_template('dashboard.html',
                           bank_count=bank_count,
                           cash_count=cash_count,
                           journal_count=journal_count,
                           sales_count=sales_count,
                           purchase_count=purchase_count,
                           total_vouchers=total_vouchers,
                           now=now)