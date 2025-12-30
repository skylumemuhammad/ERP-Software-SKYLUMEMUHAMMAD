from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import bank_vouchers, cash_vouchers, journal_vouchers, sales_vouchers, purchase_vouchers
from models import get_posting_accounts, get_account_name, log_action, reload_vouchers
from database import save_voucher_to_db
from datetime import datetime

vouchers_bp = Blueprint('vouchers', __name__, url_prefix='/vouchers')

# Storage mapping
STORAGE = {
    "bank": bank_vouchers,
    "cash": cash_vouchers,
    "journal": journal_vouchers,
    "sales": sales_vouchers,
    "purchase": purchase_vouchers
}

TEMPLATES = {
    "bank": "vouchers/bank.html",
    "cash": "vouchers/cash.html",
    "journal": "vouchers/journal.html",
    "sales": "vouchers/sales.html",
    "purchase": "vouchers/purchase.html"
}

PREFIXES = {
    "bank": "BV-",
    "cash": "CV-",
    "journal": "JV-",
    "sales": "SV-",
    "purchase": "PV-"
}

# Common handler for create and edit
def handle_voucher(vtype, index=None):
    if vtype not in STORAGE:
        flash("Invalid voucher type.", "danger")
        return redirect(url_for('dashboard.dashboard'))

    storage_list = STORAGE[vtype]
    template = TEMPLATES[vtype]
    prefix_default = PREFIXES[vtype]

    voucher = None
    if index is not None:
        if 0 <= index < len(storage_list):
            voucher = storage_list[index]
        else:
            flash("Voucher not found.", "danger")
            return redirect(url_for('vouchers.voucher_list', vtype=vtype))

    if request.method == 'POST':
        prefix = request.form['prefix'].strip()
        try:
            voucher_date = datetime.strptime(request.form['date'], "%Y-%m-%d")
        except:
            flash("Invalid voucher date.", "danger")
            return render_template(template, accounts=get_posting_accounts(), voucher=voucher, index=index, today=datetime.now().strftime('%Y-%m-%d'), prefix=prefix_default)

        cheque_date = request.form.get('cheque_date')
        if cheque_date:
            try:
                cheque_date = datetime.strptime(cheque_date, "%Y-%m-%d")
            except:
                flash("Invalid cheque date.", "danger")
                return render_template(template, accounts=get_posting_accounts(), voucher=voucher, index=index, today=datetime.now().strftime('%Y-%m-%d'), prefix=prefix_default)
        cheque_no = request.form.get('cheque_no', '').strip()

        lines = []
        accounts = request.form.getlist('account')
        descriptions = request.form.getlist('description')
        debits = request.form.getlist('debit')
        credits = request.form.getlist('credit')

        total_debit = 0
        total_credit = 0
        for i in range(len(accounts)):
            if accounts[i]:
                try:
                    debit = float(debits[i] or 0)
                    credit = float(credits[i] or 0)
                except:
                    flash("Invalid amount in line.", "danger")
                    return render_template(template, accounts=get_posting_accounts(), voucher=voucher, index=index, today=datetime.now().strftime('%Y-%m-%d'), prefix=prefix_default)

                total_debit += debit
                total_credit += credit
                lines.append({
                    "account": accounts[i],
                    "description": descriptions[i],
                    "debit": debit,
                    "credit": credit
                })

        if abs(total_debit - total_credit) > 0.01:
            flash("Error: Debit and Credit must be equal.", "danger")
            return render_template(template, accounts=get_posting_accounts(), voucher=voucher, index=index, today=datetime.now().strftime('%Y-%m-%d'), prefix=prefix_default)

        if not lines:
            flash("At least one transaction line is required.", "danger")
            return render_template(template, accounts=get_posting_accounts(), voucher=voucher, index=index, today=datetime.now().strftime('%Y-%m-%d'), prefix=prefix_default)

        new_voucher = {
            "prefix": prefix,
            "date": voucher_date,
            "cheque_date": cheque_date,
            "cheque_no": cheque_no,
            "lines": lines,
            "added_by": session['user'],
            "added_on": datetime.now()
        }

        action = "Created"
        if index is not None:
            storage_list[index] = new_voucher
            action = "Updated"
        else:
            storage_list.append(new_voucher)

        save_voucher_to_db(vtype, storage_list)
        reload_vouchers()
        log_action(session['user'], f"{action} {vtype.capitalize()} Voucher {prefix}")
        flash(f"{vtype.capitalize()} Voucher {action.lower()} successfully!", "success")
        return redirect(url_for('vouchers.voucher_list', vtype=vtype))

    # GET request - create ya edit ke liye
    accounts = get_posting_accounts()
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template(template, accounts=accounts, voucher=voucher, index=index, today=today, prefix=prefix_default)

# Create Voucher
@vouchers_bp.route('/create/<vtype>', methods=['GET', 'POST'])
def create_voucher(vtype):
    return handle_voucher(vtype)

# Edit Voucher
@vouchers_bp.route('/edit/<vtype>/<int:index>', methods=['GET', 'POST'])
def edit_voucher(vtype, index):
    return handle_voucher(vtype, index)

# View Voucher
@vouchers_bp.route('/view/<vtype>/<int:index>')
def view_voucher(vtype, index):
    if 'user' not in session:
        return redirect(url_for('auth.login'))

    if vtype not in STORAGE:
        flash("Invalid voucher type", "danger")
        return redirect(url_for('dashboard.dashboard'))

    vouchers = STORAGE[vtype]
    if 0 <= index < len(vouchers):
        voucher = vouchers[index]
        return render_template('vouchers/view.html', voucher=voucher, vtype=vtype.capitalize(), index=index, get_account_name=get_account_name)
    else:
        flash("Voucher not found", "danger")
        return redirect(url_for('vouchers.voucher_list', vtype=vtype))

# Voucher List
@vouchers_bp.route('/list/<vtype>')
def voucher_list(vtype):
    if 'user' not in session:
        return redirect(url_for('auth.login'))

    if vtype not in STORAGE:
        flash("Invalid voucher type", "danger")
        return redirect(url_for('dashboard.dashboard'))

    vouchers = STORAGE[vtype]
    return render_template('vouchers/list.html', vtype=vtype.capitalize(), vouchers=vouchers, vtype_lower=vtype)

# Delete Voucher
@vouchers_bp.route('/delete/<vtype>/<int:index>', methods=['POST'])
def delete_voucher(vtype, index):
    if 'user' not in session:
        return redirect(url_for('auth.login'))

    if vtype not in STORAGE:
        flash("Invalid voucher type", "danger")
        return redirect(url_for('dashboard.dashboard'))

    vouchers = STORAGE[vtype]
    if 0 <= index < len(vouchers):
        deleted = vouchers.pop(index)
        save_voucher_to_db(vtype, vouchers)
        reload_vouchers()
        log_action(session['user'], f"Deleted {vtype.capitalize()} Voucher {deleted.get('prefix', 'N/A')}")
        flash(f"{vtype.capitalize()} Voucher deleted successfully!", "success")
    else:
        flash("Voucher not found", "danger")

    return redirect(url_for('vouchers.voucher_list', vtype=vtype))