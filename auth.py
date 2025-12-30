from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import users, log_action

auth_bp = Blueprint('auth', __name__, url_prefix='/')

# Login
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        
        user = next((u for u in users if u['username'] == username and u['password'] == password), None)
        if user:
            session['user'] = username
            session['role'] = user.get('role', 'User')  # Role bhi session mein daalo
            log_action(username, "Logged in")
            flash("Login successful! Welcome back.", "success")
            return redirect(url_for('dashboard.dashboard'))
        else:
            flash("Invalid username or password.", "danger")
    
    return render_template('auth/login.html')

# Logout
@auth_bp.route('/logout')
def logout():
    user = session.get('user')
    if user:
        log_action(user, "Logged out")
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('auth.login'))

# User Management (Only Admin)
@auth_bp.route('/users', methods=['GET', 'POST'])
def manage_users():
    if 'user' not in session or session.get('role') != 'Admin':
        flash("Access denied. Only Admin can manage users.", "danger")
        return redirect(url_for('dashboard.dashboard'))

    global users  # Global declaration function ke top pe

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add':
            name = request.form['name'].strip()
            username = request.form['username'].strip()
            password = request.form['password'].strip()
            email = request.form['email'].strip()
            designation = request.form['designation'].strip()
            role = request.form['role']

            if not all([name, username, password, email, designation]):
                flash("All fields are required.", "danger")
            elif any(u['username'] == username for u in users):
                flash("Username already exists.", "danger")
            else:
                users.append({
                    "name": name,
                    "username": username,
                    "password": password,
                    "email": email,
                    "designation": designation,
                    "role": role
                })
                log_action(session['user'], f"Added user: {username} ({name})")
                flash(f"User '{username}' added successfully!", "success")

        elif action == 'edit':
            old_username = request.form['old_username']
            name = request.form['name'].strip()
            username = request.form['new_username'].strip()
            password = request.form['password'].strip()
            email = request.form['email'].strip()
            designation = request.form['designation'].strip()
            role = request.form['role']

            if old_username == 'admin':
                flash("Cannot edit main admin user.", "danger")
            elif any(u['username'] == username and u['username'] != old_username for u in users):
                flash("New username already exists.", "danger")
            else:
                for u in users:
                    if u['username'] == old_username:
                        u['name'] = name
                        u['username'] = username
                        u['email'] = email
                        u['designation'] = designation
                        u['role'] = role
                        if password:
                            u['password'] = password
                        break
                log_action(session['user'], f"Edited user: {old_username} → {username}")
                flash("User updated successfully!", "success")

        elif action == 'delete':
            username = request.form['username']
            if username == 'admin':
                flash("Cannot delete main admin user.", "danger")
            else:
                users[:] = [u for u in users if u['username'] != username]  # Safe remove
                log_action(session['user'], f"Deleted user: {username}")
                flash(f"User '{username}' deleted successfully!", "success")

    return render_template('auth/manage_users.html', users=users)