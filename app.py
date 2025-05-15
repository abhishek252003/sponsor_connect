from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

# DB Setup
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

# Home
@app.route('/')
def index():
    return render_template('index.html')

# Form for sponsees
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
        c.execute('INSERT INTO sponsorship_requests (org_name, event_name, category, description, email) VALUES (?, ?, ?, ?, ?)',
                  (org_name, event_name, category, description, email))
        conn.commit()
        conn.close()

        return redirect('/')
    return render_template('submit.html')

# Sponsor view
@app.route('/sponsors')
def sponsors():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('SELECT * FROM sponsorship_requests')
    rows = c.fetchall()
    conn.close()
    return render_template('sponsors.html', requests=rows)

# Admin view
@app.route('/admin')
def admin():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('SELECT * FROM sponsorship_requests')
    rows = c.fetchall()
    conn.close()
    return render_template('admin.html', requests=rows)

if __name__ == '__main__':
    app.run(debug=True)
