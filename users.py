from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import users, log_action

users_bp = Blueprint('users', __name__, url_prefix='/users')

@users_bp.route('/manage')
def manage():
    if 'user' not in session or session['user'] != 'admin':
        flash("Only admin can access user management")
        return redirect(url_for('auth.dashboard'))
    return render_template('users/manage.html', users=users.keys())

@users_bp.route('/add', methods=['POST'])
def add():
    if 'user' not in session or session['user'] != 'admin':
        flash("Access denied")
        return redirect(url_for('auth.dashboard'))
    username = request.form['username'].strip()
    password = request.form['password']
    if not username or not password:
        flash("Username and password required")
    elif username in users:
        flash("User already exists")
    else:
        users[username] = {"password": password, "role": "user"}
        log_action(session['user'], f"Added user {username}")
        flash(f"User {username} added successfully")
    return redirect(url_for('users.manage'))

@users_bp.route('/delete/<username>')
def delete(username):
    if 'user' not in session or session['user'] != 'admin':
        flash("Access denied")
        return redirect(url_for('auth.dashboard'))
    if username == 'admin':
        flash("Cannot delete admin user")
    elif username in users:
        del users[username]
        log_action(session['user'], f"Deleted user {username}")
        flash(f"User {username} deleted")
    else:
        flash("User not found")
    return redirect(url_for('users.manage'))