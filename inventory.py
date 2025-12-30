from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import items_inventory, stock_transactions, log_action
from datetime import datetime

inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')

# Helper to update current stock
def update_stock(item_code, qty_change):
    for item in items_inventory:
        if item["code"] == item_code:
            item["current_stock"] += qty_change
            break

@inventory_bp.route('/items')
def items_list():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    return render_template('inventory/items_list.html', items=items_inventory)

@inventory_bp.route('/items/add', methods=['GET', 'POST'])
def add_item():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    if request.method == 'POST':
        code = request.form['code'].upper()
        name = request.form['name']
        unit = request.form['unit']
        opening = float(request.form['opening'] or 0)
        rate = float(request.form['rate'] or 0)

        if any(item['code'] == code for item in items_inventory):
            flash("Item code already exists")
        else:
            items_inventory.append({
                "code": code,
                "name": name,
                "unit": unit,
                "opening_stock": opening,
                "rate": rate,
                "current_stock": opening
            })
            log_action(session['user'], f"Added item {code}")
            flash("Item added successfully")
            return redirect(url_for('inventory.items_list'))
    return render_template('inventory/add_item.html')

@inventory_bp.route('/stock-in', methods=['GET', 'POST'])
def stock_in():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    if request.method == 'POST':
        item_code = request.form['item']
        qty = float(request.form['qty'])
        rate = float(request.form['rate'] or 0)
        reference = request.form['reference']

        stock_transactions.append({
            "date": datetime.now(),
            "type": "in",
            "item_code": item_code,
            "qty": qty,
            "rate": rate,
            "reference": reference,
            "added_by": session['user']
        })
        update_stock(item_code, qty)
        log_action(session['user'], f"Stock In: {qty} {item_code}")
        flash("Stock In recorded successfully")
        return redirect(url_for('inventory.stock_ledger'))
    return render_template('inventory/stock_in.html', items=items_inventory)

@inventory_bp.route('/stock-out', methods=['GET', 'POST'])
def stock_out():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    if request.method == 'POST':
        item_code = request.form['item']
        qty = float(request.form['qty'])
        reference = request.form['reference']

        # Check available stock
        current = 0
        for item in items_inventory:
            if item["code"] == item_code:
                current = item["current_stock"]
                break
        if qty > current:
            flash(f"Insufficient stock. Available: {current}")
        else:
            stock_transactions.append({
                "date": datetime.now(),
                "type": "out",
                "item_code": item_code,
                "qty": qty,
                "rate": 0,  # rate optional for out
                "reference": reference,
                "added_by": session['user']
            })
            update_stock(item_code, -qty)
            log_action(session['user'], f"Stock Out: {qty} {item_code}")
            flash("Stock Out recorded successfully")
            return redirect(url_for('inventory.stock_ledger'))
    return render_template('inventory/stock_out.html', items=items_inventory)

@inventory_bp.route('/stock-ledger')
def stock_ledger():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    # Sort transactions by date
    sorted_transactions = sorted(stock_transactions, key=lambda x: x['date'], reverse=True)
    return render_template('inventory/stock_ledger.html', transactions=sorted_transactions, items=items_inventory)

@inventory_bp.route('/current-stock')
def current_stock():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    return render_template('inventory/current_stock.html', items=items_inventory)