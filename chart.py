from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import chart_of_accounts, log_action, reload_vouchers
from database import save_chart_of_accounts
import pandas as pd
import os

chart_bp = Blueprint('chart', __name__, url_prefix='/chart')

@chart_bp.route('/', methods=['GET', 'POST'])
def manage_accounts():
    if 'user' not in session:
        return redirect(url_for('auth.login'))

    global chart_of_accounts

    # Add New Account
    if request.method == 'POST' and 'add_account' in request.form:
        code = request.form['code'].strip()
        name = request.form['name'].strip()
        parent_code = request.form['parent_code'].strip() or None
        is_group = 'is_group' in request.form

        if any(acc['code'] == code for acc in chart_of_accounts):
            flash("Account code already exists!", "danger")
        else:
            new_acc = {
                "code": code,
                "name": name,
                "parent_code": parent_code,
                "is_group": is_group
            }
            chart_of_accounts.append(new_acc)
            save_chart_of_accounts(chart_of_accounts)
            reload_vouchers()
            log_action(session['user'], f"Added account {code} - {name}")
            flash("Account added successfully!", "success")

    # Edit Account
    if request.method == 'POST' and 'edit_code' in request.form:
        old_code = request.form['edit_code']
        new_code = request.form['new_code'].strip()
        name = request.form['name'].strip()
        parent_code = request.form['parent_code'].strip() or None
        is_group = 'is_group' in request.form

        updated = False
        for acc in chart_of_accounts:
            if acc['code'] == old_code:
                acc['code'] = new_code
                acc['name'] = name
                acc['parent_code'] = parent_code
                acc['is_group'] = is_group
                updated = True
                break

        if updated:
            save_chart_of_accounts(chart_of_accounts)
            reload_vouchers()
            log_action(session['user'], f"Edited account {old_code} to {new_code}")
            flash("Account updated successfully!", "success")
        else:
            flash("Account not found for editing!", "danger")

    # Delete Account
    if request.method == 'POST' and 'delete_code' in request.form:
        code = request.form['delete_code']
        old_length = len(chart_of_accounts)
        chart_of_accounts = [acc for acc in chart_of_accounts if acc['code'] != code]
        if len(chart_of_accounts) < old_length:
            save_chart_of_accounts(chart_of_accounts)
            reload_vouchers()
            log_action(session['user'], f"Deleted account {code}")
            flash("Account deleted successfully!", "success")
        else:
            flash("Account not found for deletion!", "danger")

    return render_template('chart/manage.html', accounts=chart_of_accounts)


@chart_bp.route('/import', methods=['GET', 'POST'])
def import_excel():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    
    global chart_of_accounts

    if request.method == 'POST':
        file = request.files['file']
        if not file or not file.filename.lower().endswith(('.xlsx', '.xls')):
            flash("Please select a valid Excel file (.xlsx or .xls)", "danger")
            return render_template('chart/import.html')

        try:
            temp_path = "temp_import.xlsx"
            file.save(temp_path)

            df = pd.read_excel(temp_path)
            df.columns = [str(col).strip().lower() for col in df.columns]

            if 'code' not in df.columns or 'name' not in df.columns:
                flash("Excel must have 'code' and 'name' columns.", "danger")
                os.remove(temp_path)
                return render_template('chart/import.html')

            new_accounts = []
            for _, row in df.iterrows():
                code = str(row['code']).strip()
                name = str(row['name']).strip()
                if not code or not name:
                    continue

                parent_code = None
                if 'parent_code' in df.columns:
                    pc = row.get('parent_code')
                    if pd.notna(pc):
                        parent_code = str(pc).strip()

                is_group = False
                if 'is_group' in df.columns:
                    ig = row.get('is_group')
                    if pd.notna(ig):
                        is_group = bool(ig) or str(ig).lower() in ('true', '1', 'yes', 'y')

                new_accounts.append({
                    "code": code,
                    "name": name,
                    "parent_code": parent_code,
                    "is_group": is_group
                })

            if not new_accounts:
                flash("No valid accounts found in Excel.", "danger")
                os.remove(temp_path)
                return render_template('chart/import.html')

            # Merge: existing codes overwrite, new add
            code_map = {acc['code']: acc for acc in chart_of_accounts}
            for new_acc in new_accounts:
                code_map[new_acc['code']] = new_acc

            chart_of_accounts = list(code_map.values())

            save_chart_of_accounts(chart_of_accounts)
            reload_vouchers()

            os.remove(temp_path)
            log_action(session['user'], f"Imported/Updated {len(new_accounts)} accounts from Excel")
            flash(f"Success! {len(new_accounts)} accounts imported/updated. Total accounts now: {len(chart_of_accounts)}", "success")
            return redirect(url_for('chart.manage_accounts'))

        except Exception as e:
            flash(f"Import failed: {str(e)}", "danger")
            if os.path.exists("temp_import.xlsx"):
                os.remove("temp_import.xlsx")
            return render_template('chart/import.html')
    
    return render_template('chart/import.html')