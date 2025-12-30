from flask import Blueprint, render_template, request, redirect, url_for, session, send_file, flash
from models import bank_vouchers, cash_vouchers, journal_vouchers, sales_vouchers, purchase_vouchers, logs, chart_of_accounts
from models import get_account_name, get_posting_accounts, reload_vouchers
from datetime import datetime
import pandas as pd
import os

# ReportLab for PDF
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

# Common book function (Bank, Cash, Journal, Sales, Purchase)
def common_book(vouchers_list, book_name, vtype):
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    
    data = None

    if request.method == 'POST':
        try:
            start_str = request.form['start']
            end_str = request.form['end']
            start = datetime.strptime(start_str, "%Y-%m-%d")
            end = datetime.strptime(end_str, "%Y-%m-%d")
            end = end.replace(hour=23, minute=59, second=59)
        except:
            flash("Invalid date format", "danger")
            return render_template('reports/book.html', book_name=book_name, data=data, vtype=vtype)

        filtered = [v for v in vouchers_list if start <= v['date'] <= end]
        rows = []
        for idx, v in enumerate(filtered):
            for line in v['lines']:
                rows.append({
                    "Date": v['date'].strftime("%d/%m/%Y"),
                    "Voucher": v['prefix'],
                    "Cheque No": v.get('cheque_no', ''),
                    "Account": get_account_name(line['account']),
                    "Description": line['description'],
                    "Debit": line['debit'],
                    "Credit": line['credit'],
                    "index": idx  # For actions
                })

        if rows:
            df = pd.DataFrame(rows)
            # Add action links in HTML
            df['Actions'] = df['index'].apply(lambda idx: f"""
                <a href="{url_for('vouchers.view_voucher', vtype=vtype, index=idx)}" class="btn btn-info btn-sm">View</a>
                <a href="{url_for('vouchers.edit_voucher', vtype=vtype, index=idx)}" class="btn btn-warning btn-sm">Edit</a>
                <form method="post" action="{url_for('vouchers.delete_voucher', vtype=vtype, index=idx)}" class="d-inline" onclick="return confirm('Delete this voucher?')">
                    <button type="submit" class="btn btn-danger btn-sm">Delete</button>
                </form>
            """)
            data = df.to_html(index=False, escape=False, classes="table table-striped table-bordered table-hover")
        else:
            data = "<p class='text-center text-muted'>No records found for the selected period.</p>"

        # Export Excel (exclude Actions column)
        if 'export' in request.form:
            export_df = df.drop(columns=['Actions'], errors='ignore')
            output = BytesIO()
            export_df.to_excel(output, index=False)
            output.seek(0)
            return send_file(output, download_name=f"{book_name.replace(' ', '_')}_{start_str}_to_{end_str}.xlsx", as_attachment=True)

        # Export PDF with Logo & Header
        if 'export_pdf' in request.form:
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=50, leftMargin=50, topMargin=100, bottomMargin=50)
            elements = []
            styles = getSampleStyleSheet()

            logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "logo.png")
            if os.path.exists(logo_path):
                logo = Image(logo_path, width=100, height=100)
                logo.hAlign = 'LEFT'
                elements.append(logo)
                elements.append(Spacer(1, 20))

            title_text = f"""
            <font size=18>{book_name}</font><br/>
            <font size=16>SKYLUME MUHAMMAD (PRIVATE) LIMITED</font><br/><br/>
            <font size=12>Date Range: {start_str} to {end_str}</font>
            """
            elements.append(Paragraph(title_text, styles["Title"]))
            elements.append(Spacer(1, 30))

            export_df = df.drop(columns=['Actions'], errors='ignore')
            table_data = [export_df.columns.tolist()] + export_df.values.tolist()
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ]))
            elements.append(table)

            doc.build(elements)
            buffer.seek(0)
            return send_file(buffer, as_attachment=True, download_name=f"{book_name.replace(' ', '_')}_{start_str}_to_{end_str}.pdf", mimetype='application/pdf')

    return render_template('reports/book.html', book_name=book_name, data=data, vtype=vtype)

# Books Routes
@reports_bp.route('/book/bank', methods=['GET', 'POST'])
def bank_book():
    return common_book(bank_vouchers, "Bank Book", "bank")

@reports_bp.route('/book/cash', methods=['GET', 'POST'])
def cash_book():
    return common_book(cash_vouchers, "Cash Book", "cash")

@reports_bp.route('/book/journal', methods=['GET', 'POST'])
def journal_book():
    return common_book(journal_vouchers, "Journal Book", "journal")

@reports_bp.route('/sales-book', methods=['GET', 'POST'])
def sales_book():
    return common_book(sales_vouchers, "Sales Book", "sales")

@reports_bp.route('/purchase-book', methods=['GET', 'POST'])
def purchase_book():
    return common_book(purchase_vouchers, "Purchase Book", "purchase")

# General Ledger (Individual Account Ledger)
@reports_bp.route('/account-ledger', methods=['GET', 'POST'])
def account_ledger():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    
    accounts = sorted(get_posting_accounts(), key=lambda x: x['name'])
    selected_account = None
    ledger_data = None
    start_str = end_str = ""

    if request.method == 'POST':
        account_code = request.form['account']
        try:
            start_str = request.form['start']
            end_str = request.form['end']
            start = datetime.strptime(start_str, "%Y-%m-%d")
            end = datetime.strptime(end_str, "%Y-%m-%d")
            end = end.replace(hour=23, minute=59, second=59)
        except:
            flash("Invalid date format", "danger")
            return render_template('reports/account_ledger.html', accounts=accounts)

        selected_account = next((acc for acc in chart_of_accounts if acc['code'] == account_code), None)
        if not selected_account:
            flash("Account not found", "danger")
            return render_template('reports/account_ledger.html', accounts=accounts)

        all_vouchers = bank_vouchers + cash_vouchers + journal_vouchers + sales_vouchers + purchase_vouchers
        transactions = []
        for v in all_vouchers:
            if start <= v['date'] <= end:
                for line in v['lines']:
                    if line['account'] == account_code:
                        transactions.append({
                            "date": v['date'],
                            "voucher": v['prefix'],
                            "description": line['description'],
                            "debit": line['debit'],
                            "credit": line['credit']
                        })

        transactions.sort(key=lambda x: x['date'])

        opening_balance = 0
        for v in all_vouchers:
            if v['date'] < start:
                for line in v['lines']:
                    if line['account'] == account_code:
                        opening_balance += line['debit'] - line['credit']

        rows = []
        running_balance = opening_balance
        rows.append({
            "Date": "Opening Balance",
            "Voucher": "",
            "Description": "",
            "Debit": "",
            "Credit": "",
            "Balance": f"{opening_balance:.2f}"
        })

        for trans in transactions:
            running_balance += trans['debit'] - trans['credit']
            rows.append({
                "Date": trans['date'].strftime("%d/%m/%Y"),
                "Voucher": trans['voucher'],
                "Description": trans['description'],
                "Debit": f"{trans['debit']:.2f}" if trans['debit'] > 0 else "",
                "Credit": f"{trans['credit']:.2f}" if trans['credit'] > 0 else "",
                "Balance": f"{running_balance:.2f}"
            })

        df = pd.DataFrame(rows)

        # Export Excel
        if 'export_excel' in request.form:
            output = BytesIO()
            df.to_excel(output, index=False)
            output.seek(0)
            filename = f"General_Ledger_{selected_account['name'].replace(' ', '_')}_{start_str}_to_{end_str}.xlsx"
            return send_file(output, download_name=filename, as_attachment=True)

        # Export PDF with Logo & Header
        if 'export_pdf' in request.form:
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=50, leftMargin=50, topMargin=100, bottomMargin=50)
            elements = []
            styles = getSampleStyleSheet()

            logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "logo.png")
            if os.path.exists(logo_path):
                logo = Image(logo_path, width=100, height=100)
                logo.hAlign = 'LEFT'
                elements.append(logo)
                elements.append(Spacer(1, 20))

            title_text = f"""
            <font size=18>General Ledger</font><br/>
            <font size=16>SKYLUME MUHAMMAD (PRIVATE) LIMITED</font><br/><br/>
            <font size=12>Account: {selected_account['name']} ({selected_account['code']})</font><br/>
            <font size=12>Period: {start_str} to {end_str}</font>
            """
            elements.append(Paragraph(title_text, styles["Title"]))
            elements.append(Spacer(1, 30))

            table_data = [df.columns.tolist()] + df.values.tolist()
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
            ]))
            elements.append(table)

            doc.build(elements)
            buffer.seek(0)
            filename = f"General_Ledger_{selected_account['name'].replace(' ', '_')}_{start_str}_to_{end_str}.pdf"
            return send_file(buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')

        # View with Table
        header_html = f"""
        <div class="text-center mb-4">
            <img src="/static/logo.png" alt="Logo" width="100" height="100" class="mb-3">
            <h3>SKYLUME MUHAMMAD (PRIVATE) LIMITED</h3>
            <h4>General Ledger - {selected_account['name']} ({selected_account['code']})</h4>
            <p><strong>Period:</strong> {start_str} to {end_str}</p>
            <hr>
        </div>
        """
        ledger_data = header_html + df.to_html(index=False, escape=False, classes="table table-striped table-bordered table-hover")

    return render_template('reports/account_ledger.html', 
                           accounts=accounts, 
                           selected_account=selected_account, 
                           ledger_data=ledger_data,
                           start=start_str,
                           end=end_str)

# Trial Balance
@reports_bp.route('/trial-balance', methods=['GET', 'POST'])
def trial_balance():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    
    data = None

    if request.method == 'POST':
        try:
            start_str = request.form['start']
            end_str = request.form['end']
            start = datetime.strptime(start_str, "%Y-%m-%d")
            end = datetime.strptime(end_str, "%Y-%m-%d")
            end = end.replace(hour=23, minute=59, second=59)
        except:
            flash("Invalid date format", "danger")
            return render_template('reports/trial_balance.html', data=data)

        all_vouchers = bank_vouchers + cash_vouchers + journal_vouchers + sales_vouchers + purchase_vouchers
        
        account_totals = {}
        for v in all_vouchers:
            if start <= v['date'] <= end:
                for line in v['lines']:
                    code = line['account']
                    if code not in account_totals:
                        account_totals[code] = {"debit": 0, "credit": 0}
                    account_totals[code]["debit"] += line['debit']
                    account_totals[code]["credit"] += line['credit']

        rows = []
        grand_debit = 0
        grand_credit = 0
        for code, totals in account_totals.items():
            acc_name = get_account_name(code)
            debit = totals['debit']
            credit = totals['credit']
            grand_debit += debit
            grand_credit += credit
            rows.append({
                "Account": acc_name,
                "Debit": f"{debit:.2f}" if debit > 0 else "",
                "Credit": f"{credit:.2f}" if credit > 0 else ""
            })

        rows.sort(key=lambda x: x['Account'])

        rows.append({
            "Account": "<strong>Grand Total</strong>",
            "Debit": f"<strong>{grand_debit:.2f}</strong>",
            "Credit": f"<strong>{grand_credit:.2f}</strong>"
        })

        df = pd.DataFrame(rows)
        data = df.to_html(index=False, escape=False, classes="table table-striped table-bordered")

    return render_template('reports/trial_balance.html', data=data)

# Profit & Loss
@reports_bp.route('/profit-loss', methods=['GET', 'POST'])
def profit_loss():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    
    data = None

    if request.method == 'POST':
        try:
            start_str = request.form['start']
            end_str = request.form['end']
            start = datetime.strptime(start_str, "%Y-%m-%d")
            end = datetime.strptime(end_str, "%Y-%m-%d")
            end = end.replace(hour=23, minute=59, second=59)
        except:
            flash("Invalid date format", "danger")
            return render_template('reports/profit_loss.html', data=data)

        all_vouchers = bank_vouchers + cash_vouchers + journal_vouchers + sales_vouchers + purchase_vouchers
        
        account_totals = {}
        for v in all_vouchers:
            if start <= v['date'] <= end:
                for line in v['lines']:
                    code = line['account']
                    if code not in account_totals:
                        account_totals[code] = {"debit": 0, "credit": 0}
                    account_totals[code]["debit"] += line['debit']
                    account_totals[code]["credit"] += line['credit']

        income = 0
        expense = 0
        income_accounts = []
        expense_accounts = []

        for code, totals in account_totals.items():
            acc = next((a for a in chart_of_accounts if a["code"] == code), None)
            if not acc:
                continue
            name_lower = acc["name"].lower()
            net = totals['credit'] - totals['debit']

            if "sales" in name_lower or "income" in name_lower or "revenue" in name_lower:
                income += net
                income_accounts.append({"name": acc["name"], "amount": net})
            elif "expense" in name_lower or "cost" in name_lower or "purchase" in name_lower or "exp" in name_lower:
                expense += net
                expense_accounts.append({"name": acc["name"], "amount": net})

        net_profit = income - expense

        html = "<table class='table table-bordered table-striped'>"
        html += "<thead class='table-primary'><tr><th>Particulars</th><th class='text-end'>Amount</th></tr></thead><tbody>"

        if income_accounts:
            html += "<tr class='table-info fw-bold'><td>Income</td><td></td></tr>"
            for acc in income_accounts:
                amount_str = f"{acc['amount']:.2f}" if acc['amount'] >= 0 else f"({-acc['amount']:.2f})"
                html += f"<tr><td>&nbsp;&nbsp;&nbsp;&nbsp;{acc['name']}</td><td class='text-end'>{amount_str}</td></tr>"
            html += f"<tr class='fw-bold'><td>Total Income</td><td class='text-end'>{income:.2f}</td></tr>"

        if expense_accounts:
            html += "<tr class='table-info fw-bold'><td>Expenses</td><td></td></tr>"
            for acc in expense_accounts:
                amount_str = f"{acc['amount']:.2f}" if acc['amount'] >= 0 else f"({-acc['amount']:.2f})"
                html += f"<tr><td>&nbsp;&nbsp;&nbsp;&nbsp;{acc['name']}</td><td class='text-end'>{amount_str}</td></tr>"
            html += f"<tr class='fw-bold'><td>Total Expenses</td><td class='text-end'>{expense:.2f}</td></tr>"

        color = "table-success" if net_profit >= 0 else "table-danger"
        profit_str = f"{net_profit:.2f}" if net_profit >= 0 else f"({-net_profit:.2f})"
        html += f"<tr class='{color} fw-bold fs-5'><td>Net Profit / (Loss)</td><td class='text-end'>{profit_str}</td></tr>"
        html += "</tbody></table>"
        data = html

    return render_template('reports/profit_loss.html', data=data)

# Balance Sheet
@reports_bp.route('/balance-sheet', methods=['GET', 'POST'])
def balance_sheet():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    
    data = None

    if request.method == 'POST':
        try:
            start_str = request.form['start']
            end_str = request.form['end']
            start = datetime.strptime(start_str, "%Y-%m-%d")
            end = datetime.strptime(end_str, "%Y-%m-%d")
            end = end.replace(hour=23, minute=59, second=59)
        except:
            flash("Invalid date format", "danger")
            return render_template('reports/balance_sheet.html', data=data)

        all_vouchers = bank_vouchers + cash_vouchers + journal_vouchers + sales_vouchers + purchase_vouchers
        
        account_balances = {}
        for v in all_vouchers:
            if v['date'] <= end:
                for line in v['lines']:
                    code = line['account']
                    account_balances[code] = account_balances.get(code, 0) + line['debit'] - line['credit']

        def get_balance(code):
            return account_balances.get(code, 0)

        def get_children(parent_code):
            return [acc for acc in chart_of_accounts if acc.get("parent_code") == parent_code]

        assets = {"total": 0, "subgroups": []}
        liabilities = {"total": 0, "subgroups": []}
        equity = {"total": 0, "subgroups": []}

        for acc in chart_of_accounts:
            if not acc.get("parent_code"):
                name_lower = acc["name"].lower()
                code = acc["code"]
                total_balance = get_balance(code)

                children = get_children(code)
                for child in children:
                    total_balance += get_balance(child["code"])
                    grand = get_children(child["code"])
                    for g in grand:
                        total_balance += get_balance(g["code"])

                subgroup = {"name": acc["name"], "total": total_balance}

                if "asset" in name_lower or "cash" in name_lower or "bank" in name_lower:
                    assets["subgroups"].append(subgroup)
                    assets["total"] += total_balance
                elif "liability" in name_lower or "payable" in name_lower:
                    liabilities["subgroups"].append(subgroup)
                    liabilities["total"] += total_balance
                elif "equity" in name_lower or "capital" in name_lower:
                    equity["subgroups"].append(subgroup)
                    equity["total"] += total_balance

        total_assets = assets["total"]
        total_le = liabilities["total"] + equity["total"]

        html = "<table class='table table-bordered table-striped'>"
        html += "<thead class='table-primary'><tr><th>Particulars</th><th class='text-end'>Amount</th></tr></thead><tbody>"

        html += "<tr class='table-info fw-bold fs-5'><td colspan='2'>Assets</td></tr>"
        for sg in assets["subgroups"]:
            amount_str = f"{sg['total']:.2f}" if sg['total'] >= 0 else f"({-sg['total']:.2f})"
            html += f"<tr class='table-light fw-bold'><td>&nbsp;&nbsp;{sg['name']}</td><td class='text-end'>{amount_str}</td></tr>"
        html += f"<tr class='table-success fw-bold'><td>Total Assets</td><td class='text-end'>{total_assets:.2f}</td></tr>"

        html += "<tr class='table-info fw-bold fs-5'><td colspan='2'>Liabilities</td></tr>"
        for sg in liabilities["subgroups"]:
            amount_str = f"{sg['total']:.2f}" if sg['total'] >= 0 else f"({-sg['total']:.2f})"
            html += f"<tr class='table-light fw-bold'><td>&nbsp;&nbsp;{sg['name']}</td><td class='text-end'>{amount_str}</td></tr>"
        html += f"<tr class='fw-bold'><td>Total Liabilities</td><td class='text-end'>{liabilities['total']:.2f}</td></tr>"

        html += "<tr class='table-info fw-bold fs-5'><td colspan='2'>Equity</td></tr>"
        for sg in equity["subgroups"]:
            amount_str = f"{sg['total']:.2f}" if sg['total'] >= 0 else f"({-sg['total']:.2f})"
            html += f"<tr class='table-light fw-bold'><td>&nbsp;&nbsp;{sg['name']}</td><td class='text-end'>{amount_str}</td></tr>"
        html += f"<tr class='fw-bold'><td>Total Equity</td><td class='text-end'>{equity['total']:.2f}</td></tr>"

        color = "table-success" if abs(total_assets - total_le) < 0.01 else "table-danger"
        html += f"<tr class='{color} fw-bold fs-5'><td>Total Liabilities & Equity</td><td class='text-end'>{total_le:.2f}</td></tr>"
        html += "</tbody></table>"

        if abs(total_assets - total_le) > 0.01:
            html += f"<div class='alert alert-danger mt-4'>Warning: Balance Sheet not balanced! Difference: {total_assets - total_le:.2f}</div>"

        data = html

    return render_template('reports/balance_sheet.html', data=data)

# Users Log
@reports_bp.route('/users-log', methods=['GET', 'POST'])
def users_log():
    if 'user' not in session:
        return redirect(url_for('auth.login'))

    # Reload logs fresh
    reload_vouchers()  # Yeh logs bhi reload kar dega

    # Filter logic (optional date range)
    filtered_logs = logs
    if request.method == 'POST':
        try:
            start_str = request.form.get('start')
            end_str = request.form.get('end')
            if start_str and end_str:
                start = datetime.strptime(start_str, "%Y-%m-%d")
                end = datetime.strptime(end_str, "%Y-%m-%d")
                end = end.replace(hour=23, minute=59, second=59)
                filtered_logs = [log for log in logs if start <= datetime.strptime(log['timestamp'], "%Y-%m-%d %H:%M:%S") <= end]
        except:
            flash("Invalid date format for filter", "danger")

    # Export Excel
    if 'export_excel' in request.form:
        df = pd.DataFrame(filtered_logs)
        output = BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)
        return send_file(output, download_name=f"Users_Log_{datetime.now().strftime('%Y%m%d')}.xlsx", as_attachment=True)

    return render_template('reports/users_log.html', logs=filtered_logs)

# Chart of Accounts Book (Hierarchical View)
@reports_bp.route('/coa')
def coa_book():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    
    # Tree banane ke liye
    tree = []
    
    if chart_of_accounts:
        # Fast lookup dict
        acc_dict = {acc['code']: acc.copy() for acc in chart_of_accounts}
        
        # Root level (parent_code None)
        roots = [acc for acc in chart_of_accounts if not acc.get("parent_code")]
        
        def build_tree(node):
            children = []
            for code, acc in acc_dict.items():
                if acc.get("parent_code") == node['code']:
                    child_node = acc.copy()
                    child_node['children'] = build_tree(child_node)
                    children.append(child_node)
            return children
        
        for root in roots:
            root_node = root.copy()
            root_node['children'] = build_tree(root_node)
            tree.append(root_node)

    return render_template('reports/coa_book.html', tree=tree, accounts=chart_of_accounts)