from flask import Flask, render_template, request, redirect, url_for, session, make_response
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///employees.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Predefined users ---
USERS = {
    'user1': 'password1',
    'user2': 'password2',
    'user3': 'password3'
}

# --- Employee model ---
class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    aadhar_number = db.Column(db.String(20), unique=True, nullable=False)
    raised_by = db.Column(db.String(50), nullable=False)
    reason = db.Column(db.String(200), nullable=False)
    police_complaint_logged = db.Column(db.Boolean, nullable=False)
    fir_number = db.Column(db.String(50), nullable=True)

# --- Routes ---
@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if USERS.get(username) == password:
            session['user'] = username
            return redirect(url_for('add_employee'))
        else:
            return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

@app.route('/add', methods=['GET', 'POST'])
def add_employee():
    if 'user' not in session:
        return redirect(url_for('login'))

    message = None
    error = None

    if request.method == 'POST':
        name = request.form['name']
        aadhar_number = request.form['aadhar']
        raised_by = request.form['raised_by']
        reason = request.form['reason']
        police_complaint_logged = request.form.get('police_complaint') == 'yes'
        fir_number = request.form['fir_number'] if police_complaint_logged else None

        emp = Employee(
            name=name,
            aadhar_number=aadhar_number,
            raised_by=raised_by,
            reason=reason,
            police_complaint_logged=police_complaint_logged,
            fir_number=fir_number
        )

        try:
            db.session.add(emp)
            db.session.commit()
            message = "Employee details added successfully."
        except Exception as e:
            db.session.rollback()
            error = "Employee with this Aadhar number already exists."

    employees = Employee.query.all()
    return render_template('add.html', message=message, error=error, employees=employees)

@app.route('/search', methods=['GET', 'POST'])
def search():
    result = []
    searched = False

    if request.method == 'POST':
        query = request.form['query'].strip().lower()
        searched = True

        # Search by name (case-insensitive)
        result = Employee.query.filter(
            db.func.lower(Employee.name).like(f"%{query}%")
        ).all()

        # Also search by Aadhar number if no results are found by name
        if not result:
            exact = Employee.query.filter(Employee.aadhar_number == query).first()
            if exact:
                result = [exact]

    return render_template('search.html', result=result, searched=searched)

@app.route('/delete/<int:emp_id>', methods=['POST'])
def delete_employee(emp_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    employee = Employee.query.get_or_404(emp_id)
    db.session.delete(employee)
    db.session.commit()
    return redirect(url_for('add_employee'))


@app.route('/edit/<int:emp_id>', methods=['GET', 'POST'])
def edit_employee(emp_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    employee = Employee.query.get_or_404(emp_id)

    if request.method == 'POST':
        employee.name = request.form['name']
        employee.aadhar_number = request.form['aadhar']
        employee.raised_by = request.form['raised_by']
        employee.reason = request.form['reason']
        employee.police_complaint_logged = request.form.get('police_complaint') == 'yes'
        employee.fir_number = request.form['fir_number'] if employee.police_complaint_logged else None

        db.session.commit()
        return redirect(url_for('add_employee'))

    return render_template('edit.html', employee=employee)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)