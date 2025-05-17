import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///employees.db'
app.config['SECRET_KEY'] = 'secretkey123'

# Gmail settings
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'george.sesay2022@gmail.com'
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')

mail = Mail(app)
s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
db = SQLAlchemy(app)

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(10), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(50), nullable=False)
    position = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True)
    phone = db.Column(db.String(20))
    tax_pin = db.Column(db.String(20))
    hire_date = db.Column(db.Date)
    status = db.Column(db.String(10), default='Active')
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
               
with app.app_context():
    db.create_all()
    if not Employee.query.filter_by(employee_id='ADMIN').first():
        admin = Employee(
            employee_id='ADMIN',
            full_name='Admin',
            department='Admin',
            position='System Admin',
            email='george.sesay2022@gmail.com',
            hire_date=datetime.utcnow(),
            status='Active'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()

@app.route('/')
def index():
    if 'employee_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/invite', methods=['GET', 'POST'])
def invite():
    if 'employee_id' not in session or session['employee_id'] != 'ADMIN':
        return redirect(url_for('login'))

    if request.method == 'POST':
        email = request.form['email']
        if not email:
            flash('Please enter a valid email address.')
            return redirect(url_for('invite'))

        token = s.dumps(email, salt='email-invite')
        link = url_for('register', token=token, _external=True)
        try:
            msg = Message('SalimTrading Staff Registration',
                          sender=app.config['MAIL_USERNAME'],
                          recipients=[email])
            msg.body = f'Register here: {link}'
            mail.send(msg)
            flash(f'Invite sent to {email}')
        except Exception as e:
            flash(f'Failed to send email: {str(e)}')
            print("Error sending email:", e)
    return render_template('invite.html')

@app.route('/register/<token>', methods=['GET', 'POST'])
def register(token):
    try:
        email = s.loads(token, salt='email-invite', max_age=3600)
    except (SignatureExpired, BadSignature):
        return '<h3>Invalid or expired token.</h3>'
    if request.method == 'POST':
        new_emp = Employee(
            employee_id=request.form['employee_id'],
            full_name=request.form['full_name'],
            department=request.form['department'],
            position=request.form['position'],
            email=email,
            hire_date=datetime.strptime(request.form['hire_date'], '%Y-%m-%d'),
            status='Active'
        )
        new_emp.set_password(request.form['password'])
        db.session.add(new_emp)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register_token.html', email=email)

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = Employee.query.filter_by(email=email).first()
        if user:
            token = s.dumps(email, salt='reset-pass')
            link = url_for('reset_password', token=token, _external=True)
            msg = Message('Reset Your Password', sender=app.config['MAIL_USERNAME'], recipients=[email])
            msg.body = f'Reset password: {link}'
            mail.send(msg)
        flash('If your email exists, a reset link has been sent.')
    return render_template('forgot_password.html')

@app.route('/reset/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = s.loads(token, salt='reset-pass', max_age=3600)
    except (SignatureExpired, BadSignature):
        return '<h3>Invalid or expired token.</h3>'
    user = Employee.query.filter_by(email=email).first()
    if request.method == 'POST':
        user.set_password(request.form['password'])
        db.session.commit()
        flash('Password updated.')
        return redirect(url_for('login'))
    return render_template('reset_password.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        emp = Employee.query.filter_by(employee_id=request.form['employee_id']).first()
        if emp and emp.check_password(request.form['password']):
            session['employee_id'] = emp.employee_id
            return redirect(url_for('index'))
        flash("Invalid login")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('employee_id', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
   
    port = int(os.environ.get('PORT', 5000))  # Render provides PORT
    app.run(host='0.0.0.0', port=port)

