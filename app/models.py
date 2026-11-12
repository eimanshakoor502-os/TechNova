from datetime import datetime, date
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager


# Project aur Employees ke beech many-to-many link
project_members = db.Table(
    "project_members",
    db.Column("project_id", db.Integer, db.ForeignKey("projects.id"), primary_key=True),
    db.Column("employee_id", db.Integer, db.ForeignKey("employees.id"), primary_key=True),
)


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="employee")  # admin / manager / employee
    is_active_user = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_active(self):
        return self.is_active_user


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


class Department(db.Model):
    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255))
    employees = db.relationship("Employee", backref="department", lazy=True)


class Employee(db.Model):
    __tablename__ = "employees"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(30))
    designation = db.Column(db.String(100))
    salary = db.Column(db.Numeric(10, 2))
    join_date = db.Column(db.Date, default=date.today)
    status = db.Column(db.String(20), default="Active")
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))

    tasks = db.relationship("Task", backref="assignee", lazy=True)
    assets = db.relationship("Asset", backref="holder", lazy=True)


class Client(db.Model):
    __tablename__ = "clients"

    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(150), nullable=False)
    contact_person = db.Column(db.String(100))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(30))
    address = db.Column(db.String(255))
    projects = db.relationship("Project", backref="client", lazy=True)


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.Date)
    deadline = db.Column(db.Date)
    status = db.Column(db.String(20), default="Active")  # Active / On Hold / Completed
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"))

    members = db.relationship("Employee", secondary=project_members, backref="projects")
    tasks = db.relationship("Task", backref="project", lazy=True)


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default="Pending")  # Pending / In Progress / Done
    priority = db.Column(db.String(20), default="Medium")  # Low / Medium / High
    due_date = db.Column(db.Date)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"))
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"))


class Asset(db.Model):
    __tablename__ = "assets"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    asset_type = db.Column(db.String(50))  # Laptop / Monitor / Phone ...
    serial_number = db.Column(db.String(100), unique=True)
    status = db.Column(db.String(20), default="Available")  # Available / Assigned / Repair
    purchase_date = db.Column(db.Date)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"))


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    action = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship("User", backref="logs")