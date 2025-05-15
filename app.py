from flask import Flask, render_template, request, redirect, flash, url_for
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from flask_bcrypt import Bcrypt
import sqlite3

app = Flask(__name__)
app.secret_key = 'ABHIshek@1234'

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Flash message for unauthorized access
@login_manager.unauthorized_handler
def unauthorized():
    flash('Please log in to access this page.', 'warning')
    return redirect(url_for('login'))

bcrypt = Bcrypt(app)

# --- User class ---
class User(UserMixin):
    def __init__(self, id, username, role):
        self.id = id
        self.username = username
        self.role = role

# --- Initialize DB ---
def init_db():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS sponsorship_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            org_name TEXT,
            event_name TEXT,
            category TEXT,
            description TEXT,
            email TEXT,
            status TEXT DEFAULT 'pending'
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- Load user for login manager ---
@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user_data = c.fetchone()
    conn.close()
    if user_data:
        return User(user_data[0], user_data[1], user_data[3])
    return None

# --- Routes ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['GET', 'POST'])
@login_required
def submit():
    if request.method == 'POST':
        org_name = request.form['org_name']
        event_name = request.form['event_name']
        category = request.form['category']
        description = request.form['description']
        email = request.form['email']

        conn = sqlite3.connect('data.db')
        c = conn.cursor()
        c.execute('''
            INSERT INTO sponsorship_requests (org_name, event_name, category, description, email)
            VALUES (?, ?, ?, ?, ?)
        ''', (org_name, event_name, category, description, email))
        conn.commit()
        conn.close()

        flash('Sponsorship request submitted successfully!', 'success')
        return redirect('/')
    return render_template('submit.html')

@app.route('/sponsors')
@login_required
def sponsors():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('SELECT * FROM sponsorship_requests')
    rows = c.fetchall()
    conn.close()
    return render_template('sponsors.html', requests=rows)

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if current_user.role != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect('/')
    
    search_query = request.args.get('search', '')
    status_filter = request.args.get('status', '')

    conn = sqlite3.connect('data.db')
    c = conn.cursor()

    query = 'SELECT * FROM sponsorship_requests WHERE 1=1'
    params = []

    if search_query:
        query += ' AND (org_name LIKE ? OR event_name LIKE ? OR category LIKE ? OR description LIKE ?)'
        params.extend([f'%{search_query}%'] * 4)

    if status_filter:
        query += ' AND status = ?'
        params.append(status_filter)

    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    
    return render_template('admin.html', requests=rows, search_query=search_query, status_filter=status_filter)

@app.route('/admin/delete/<int:request_id>', methods=['POST'])
@login_required
def delete_request(request_id):
    if current_user.role != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect('/')

    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    
    # Delete the request from the database using its ID
    c.execute('DELETE FROM sponsorship_requests WHERE id = ?', (request_id,))
    conn.commit()
    conn.close()

    flash('Sponsorship request deleted successfully!', 'success')
    return redirect(url_for('admin'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('data.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username = ?', (username,))
        user_data = c.fetchone()
        conn.close()

        if user_data and bcrypt.check_password_hash(user_data[2], password):
            user = User(user_data[0], user_data[1], user_data[3])
            login_user(user)
            flash('Login successful', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials', 'danger')

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        try:
            conn = sqlite3.connect('data.db')
            c = conn.cursor()
            c.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
                      (username, hashed_password, role))
            conn.commit()
            conn.close()
            flash('User registered successfully!', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists.', 'danger')

    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'info')
    return redirect(url_for('login'))

# --- Approve Request ---
@app.route('/approve_request/<int:request_id>')
@login_required
def approve_request(request_id):
    if current_user.role != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect('/')
    
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('UPDATE sponsorship_requests SET status = ? WHERE id = ?', ('approved', request_id))
    conn.commit()
    conn.close()
    
    flash('Request approved!', 'success')
    return redirect(url_for('admin'))

# --- Reject Request ---
@app.route('/reject_request/<int:request_id>')
@login_required
def reject_request(request_id):
    if current_user.role != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect('/')
    
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('UPDATE sponsorship_requests SET status = ? WHERE id = ?', ('rejected', request_id))
    conn.commit()
    conn.close()
    
    flash('Request rejected!', 'danger')
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
