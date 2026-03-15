from flask import Flask, render_template, redirect, url_for
from clouddrive import create_app
from clouddrive.auth import get_current_user_id

app = create_app()


@app.route('/')
def index():
    if get_current_user_id():
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/register')
def register():
    return render_template('login.html', register=True)


@app.route('/dashboard')
def dashboard():
    if not get_current_user_id():
        return redirect(url_for('login'))
    return render_template('dashboard.html')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5051)
