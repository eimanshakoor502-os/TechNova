from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Employee, Department, AuditLog
from app.decorators import roles_required

employees_bp = Blueprint("employees", __name__)


def log_action(text):
    db.session.add(AuditLog(user_id=current_user.id, action=text))


# ---------- DEPARTMENTS ----------

@employees_bp.route("/departments")
@login_required
@roles_required("admin", "manager")
def departments():
    items = Department.query.order_by(Department.name).all()
    return render_template("departments/list.html", departments=items)


@employees_bp.route("/departments/add", methods=["POST"])
@login_required
@roles_required("admin")
def department_add():
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()

    if not name:
        flash("Department ka naam zaroori hai.", "danger")
    elif Department.query.filter_by(name=name).first():
        flash("Ye department pehle se maujood hai.", "danger")
    else:
        db.session.add(Department(name=name, description=description))
        log_action(f"Department added: {name}")
        db.session.commit()
        flash("Department add ho gaya.", "success")
    return redirect(url_for("employees.departments"))


@employees_bp.route("/departments/<int:dept_id>/delete", methods=["POST"])
@login_required
@roles_required("admin")
def department_delete(dept_id):
    dept = db.get_or_404(Department, dept_id)
    if dept.employees:
        flash("Is department mein employees hain, pehle unhein shift karo.", "danger")
    else:
        log_action(f"Department deleted: {dept.name}")
        db.session.delete(dept)
        db.session.commit()
        flash("Department delete ho gaya.", "success")
    return redirect(url_for("employees.departments"))


# ---------- EMPLOYEES ----------

@employees_bp.route("/employees")
@login_required
@roles_required("admin", "manager")
def employee_list():
    q = request.args.get("q", "").strip()
    query = Employee.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            Employee.full_name.ilike(like)
            | Employee.email.ilike(like)
            | Employee.designation.ilike(like)
        )
    items = query.order_by(Employee.full_name).all()
    return render_template("employees/list.html", employees=items, q=q)


@employees_bp.route("/employees/add", methods=["GET", "POST"])
@login_required
@roles_required("admin", "manager")
def employee_add():
    departments = Department.query.order_by(Department.name).all()

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        full_name = request.form.get("full_name", "").strip()

        if not full_name or not email:
            flash("Naam aur email zaroori hain.", "danger")
        elif Employee.query.filter_by(email=email).first():
            flash("Is email ka employee pehle se maujood hai.", "danger")
        else:
            emp = Employee(
                full_name=full_name,
                email=email,
                phone=request.form.get("phone", "").strip(),
                designation=request.form.get("designation", "").strip(),
                salary=request.form.get("salary") or None,
                status=request.form.get("status", "Active"),
                department_id=request.form.get("department_id") or None,
            )
            db.session.add(emp)
            log_action(f"Employee added: {full_name}")
            db.session.commit()
            flash("Employee add ho gaya.", "success")
            return redirect(url_for("employees.employee_list"))

    return render_template("employees/form.html", employee=None, departments=departments)


@employees_bp.route("/employees/<int:emp_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required("admin", "manager")
def employee_edit(emp_id):
    emp = db.get_or_404(Employee, emp_id)
    departments = Department.query.order_by(Department.name).all()

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        other = Employee.query.filter(Employee.email == email, Employee.id != emp.id).first()

        if other:
            flash("Ye email kisi aur employee ka hai.", "danger")
        else:
            emp.full_name = request.form.get("full_name", "").strip()
            emp.email = email
            emp.phone = request.form.get("phone", "").strip()
            emp.designation = request.form.get("designation", "").strip()
            emp.salary = request.form.get("salary") or None
            emp.status = request.form.get("status", "Active")
            emp.department_id = request.form.get("department_id") or None
            log_action(f"Employee updated: {emp.full_name}")
            db.session.commit()
            flash("Employee update ho gaya.", "success")
            return redirect(url_for("employees.employee_list"))

    return render_template("employees/form.html", employee=emp, departments=departments)


@employees_bp.route("/employees/<int:emp_id>/delete", methods=["POST"])
@login_required
@roles_required("admin")
def employee_delete(emp_id):
    emp = db.get_or_404(Employee, emp_id)
    if emp.tasks or emp.assets:
        flash("Is employee ke tasks ya assets hain, pehle unhein hata do.", "danger")
    else:
        log_action(f"Employee deleted: {emp.full_name}")
        db.session.delete(emp)
        db.session.commit()
        flash("Employee delete ho gaya.", "success")
    return redirect(url_for("employees.employee_list"))