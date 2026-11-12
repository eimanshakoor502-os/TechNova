from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import func
from app import db
from app.models import User, Employee, AuditLog, Project, Task, Asset, Department
from app.decorators import roles_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

ROLES = ["admin", "manager", "employee"]


def log_action(text):
    db.session.add(AuditLog(user_id=current_user.id, action=text))


def active_admin_count():
    return User.query.filter_by(role="admin", is_active_user=True).count()


# ---------- USERS ----------

@admin_bp.route("/users")
@login_required
@roles_required("admin")
def user_list():
    items = User.query.order_by(User.username).all()
    return render_template("admin/users.html", users=items)


@admin_bp.route("/users/add", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def user_add():
    employees = Employee.query.order_by(Employee.full_name).all()

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "employee")

        if not username or not email or len(password) < 6:
            flash("Username, email zaroori hain aur password kam az kam 6 characters ka ho.", "danger")
        elif role not in ROLES:
            flash("Role sahi nahi hai.", "danger")
        elif User.query.filter_by(username=username).first():
            flash("Ye username pehle se maujood hai.", "danger")
        elif User.query.filter_by(email=email).first():
            flash("Ye email pehle se maujood hai.", "danger")
        else:
            user = User(
                username=username,
                email=email,
                role=role,
                employee_id=request.form.get("employee_id") or None,
            )
            user.set_password(password)
            db.session.add(user)
            log_action(f"User created: {username} ({role})")
            db.session.commit()
            flash("User ban gaya.", "success")
            return redirect(url_for("admin.user_list"))

    return render_template("admin/user_form.html", user=None, employees=employees, roles=ROLES)


@admin_bp.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def user_edit(user_id):
    user = db.get_or_404(User, user_id)
    employees = Employee.query.order_by(Employee.full_name).all()

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        role = request.form.get("role", user.role)
        password = request.form.get("password", "")
        is_active = request.form.get("is_active") == "1"

        other = User.query.filter(User.email == email, User.id != user.id).first()
        losing_admin = user.role == "admin" and user.is_active_user and (role != "admin" or not is_active)

        if not email:
            flash("Email zaroori hai.", "danger")
        elif other:
            flash("Ye email kisi aur user ka hai.", "danger")
        elif role not in ROLES:
            flash("Role sahi nahi hai.", "danger")
        elif password and len(password) < 6:
            flash("Naya password kam az kam 6 characters ka ho.", "danger")
        elif losing_admin and active_admin_count() <= 1:
            flash("Aakhri active admin ko change ya disable nahi kar sakte.", "danger")
        else:
            user.email = email
            user.role = role
            user.is_active_user = is_active
            user.employee_id = request.form.get("employee_id") or None
            if password:
                user.set_password(password)
            log_action(f"User updated: {user.username} ({role})")
            db.session.commit()
            flash("User update ho gaya.", "success")
            return redirect(url_for("admin.user_list"))

    return render_template("admin/user_form.html", user=user, employees=employees, roles=ROLES)


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
@roles_required("admin")
def user_delete(user_id):
    user = db.get_or_404(User, user_id)
    if user.id == current_user.id:
        flash("Apna account delete nahi kar sakte.", "danger")
    elif user.role == "admin" and active_admin_count() <= 1:
        flash("Aakhri admin delete nahi ho sakta.", "danger")
    else:
        # Is user ke purane audit logs ka user khali kar do, record bacha rahe
        AuditLog.query.filter_by(user_id=user.id).update({"user_id": None})
        log_action(f"User deleted: {user.username}")
        db.session.delete(user)
        db.session.commit()
        flash("User delete ho gaya.", "success")
    return redirect(url_for("admin.user_list"))


# ---------- AUDIT LOGS ----------

@admin_bp.route("/audit-logs")
@login_required
@roles_required("admin")
def audit_logs():
    page = request.args.get("page", 1, type=int)
    pagination = AuditLog.query.order_by(AuditLog.created_at.desc()).paginate(
        page=page, per_page=25, error_out=False
    )
    return render_template("admin/audit_logs.html", pagination=pagination)


# ---------- REPORTS ----------

@admin_bp.route("/reports")
@login_required
@roles_required("admin")
def reports():
    tasks_by_status = dict(db.session.query(Task.status, func.count(Task.id)).group_by(Task.status).all())
    projects_by_status = dict(db.session.query(Project.status, func.count(Project.id)).group_by(Project.status).all())
    assets_by_status = dict(db.session.query(Asset.status, func.count(Asset.id)).group_by(Asset.status).all())
    employees_by_dept = (
        db.session.query(Department.name, func.count(Employee.id))
        .outerjoin(Employee, Employee.department_id == Department.id)
        .group_by(Department.name)
        .order_by(Department.name)
        .all()
    )
    workload = (
        db.session.query(Employee.full_name, func.count(Task.id))
        .outerjoin(Task, (Task.employee_id == Employee.id) & (Task.status != "Done"))
        .group_by(Employee.full_name)
        .order_by(Employee.full_name)
        .all()
    )
    return render_template(
        "admin/reports.html",
        tasks_by_status=tasks_by_status,
        projects_by_status=projects_by_status,
        assets_by_status=assets_by_status,
        employees_by_dept=employees_by_dept,
        workload=workload,
    )