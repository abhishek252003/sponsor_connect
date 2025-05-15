from flask import Flask, render_template, request, redirect
import sqlite3
import os

app = Flask(__name__)

# --- DATABASE SETUP ---
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
            email TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- ROUTES ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['GET', 'POST'])
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

        return redirect('/')
    return render_template('submit.html')

@app.route('/sponsors')
def sponsors():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('SELECT * FROM sponsorship_requests')
    rows = c.fetchall()
    conn.close()
    return render_template('sponsors.html', requests=rows)

@app.route('/admin')
def admin():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('SELECT * FROM sponsorship_requests')
    rows = c.fetchall()
    conn.close()
    return render_template('admin.html', requests=rows)

# --- MAIN ENTRY POINT ---
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
