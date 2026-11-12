from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.models import Client, Project, Task, Employee, AuditLog
from app.decorators import roles_required

work_bp = Blueprint("work", __name__)

TASK_STATUSES = ["Pending", "In Progress", "Done"]
PROJECT_STATUSES = ["Active", "On Hold", "Completed"]
PRIORITIES = ["Low", "Medium", "High"]


def log_action(text):
    db.session.add(AuditLog(user_id=current_user.id, action=text))


def parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


# ---------- CLIENTS ----------

@work_bp.route("/clients")
@login_required
@roles_required("admin", "manager")
def client_list():
    items = Client.query.order_by(Client.company_name).all()
    return render_template("clients/list.html", clients=items)


@work_bp.route("/clients/add", methods=["GET", "POST"])
@login_required
@roles_required("admin", "manager")
def client_add():
    if request.method == "POST":
        name = request.form.get("company_name", "").strip()
        if not name:
            flash("Company ka naam zaroori hai.", "danger")
        else:
            client = Client(
                company_name=name,
                contact_person=request.form.get("contact_person", "").strip(),
                email=request.form.get("email", "").strip(),
                phone=request.form.get("phone", "").strip(),
                address=request.form.get("address", "").strip(),
            )
            db.session.add(client)
            log_action(f"Client added: {name}")
            db.session.commit()
            flash("Client add ho gaya.", "success")
            return redirect(url_for("work.client_list"))
    return render_template("clients/form.html", client=None)


@work_bp.route("/clients/<int:client_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required("admin", "manager")
def client_edit(client_id):
    client = db.get_or_404(Client, client_id)
    if request.method == "POST":
        name = request.form.get("company_name", "").strip()
        if not name:
            flash("Company ka naam zaroori hai.", "danger")
        else:
            client.company_name = name
            client.contact_person = request.form.get("contact_person", "").strip()
            client.email = request.form.get("email", "").strip()
            client.phone = request.form.get("phone", "").strip()
            client.address = request.form.get("address", "").strip()
            log_action(f"Client updated: {name}")
            db.session.commit()
            flash("Client update ho gaya.", "success")
            return redirect(url_for("work.client_list"))
    return render_template("clients/form.html", client=client)


@work_bp.route("/clients/<int:client_id>/delete", methods=["POST"])
@login_required
@roles_required("admin")
def client_delete(client_id):
    client = db.get_or_404(Client, client_id)
    if client.projects:
        flash("Is client ke projects hain, pehle unhein hata do.", "danger")
    else:
        log_action(f"Client deleted: {client.company_name}")
        db.session.delete(client)
        db.session.commit()
        flash("Client delete ho gaya.", "success")
    return redirect(url_for("work.client_list"))


# ---------- PROJECTS ----------

def selected_members():
    ids = [int(i) for i in request.form.getlist("members") if i.isdigit()]
    if not ids:
        return []
    return Employee.query.filter(Employee.id.in_(ids)).all()


@work_bp.route("/projects")
@login_required
@roles_required("admin", "manager")
def project_list():
    items = Project.query.order_by(Project.deadline).all()
    return render_template("projects/list.html", projects=items)


@work_bp.route("/projects/add", methods=["GET", "POST"])
@login_required
@roles_required("admin", "manager")
def project_add():
    clients = Client.query.order_by(Client.company_name).all()
    employees = Employee.query.order_by(Employee.full_name).all()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Project ka naam zaroori hai.", "danger")
        else:
            project = Project(
                name=name,
                description=request.form.get("description", "").strip(),
                start_date=parse_date(request.form.get("start_date")),
                deadline=parse_date(request.form.get("deadline")),
                status=request.form.get("status", "Active"),
                client_id=request.form.get("client_id") or None,
            )
            project.members = selected_members()
            db.session.add(project)
            log_action(f"Project added: {name}")
            db.session.commit()
            flash("Project add ho gaya.", "success")
            return redirect(url_for("work.project_list"))

    return render_template("projects/form.html", project=None, clients=clients,
                           employees=employees, statuses=PROJECT_STATUSES)


@work_bp.route("/projects/<int:project_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required("admin", "manager")
def project_edit(project_id):
    project = db.get_or_404(Project, project_id)
    clients = Client.query.order_by(Client.company_name).all()
    employees = Employee.query.order_by(Employee.full_name).all()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Project ka naam zaroori hai.", "danger")
        else:
            project.name = name
            project.description = request.form.get("description", "").strip()
            project.start_date = parse_date(request.form.get("start_date"))
            project.deadline = parse_date(request.form.get("deadline"))
            project.status = request.form.get("status", "Active")
            project.client_id = request.form.get("client_id") or None
            project.members = selected_members()
            log_action(f"Project updated: {name}")
            db.session.commit()
            flash("Project update ho gaya.", "success")
            return redirect(url_for("work.project_list"))

    return render_template("projects/form.html", project=project, clients=clients,
                           employees=employees, statuses=PROJECT_STATUSES)


@work_bp.route("/projects/<int:project_id>/delete", methods=["POST"])
@login_required
@roles_required("admin")
def project_delete(project_id):
    project = db.get_or_404(Project, project_id)
    if project.tasks:
        flash("Is project ke tasks hain, pehle unhein hata do.", "danger")
    else:
        log_action(f"Project deleted: {project.name}")
        db.session.delete(project)
        db.session.commit()
        flash("Project delete ho gaya.", "success")
    return redirect(url_for("work.project_list"))


# ---------- TASKS ----------

@work_bp.route("/tasks")
@login_required
def task_list():
    if current_user.role in ("admin", "manager"):
        items = Task.query.order_by(Task.due_date).all()
    elif current_user.employee_id:
        items = Task.query.filter_by(employee_id=current_user.employee_id).order_by(Task.due_date).all()
    else:
        items = []
    return render_template("tasks/list.html", tasks=items, statuses=TASK_STATUSES)


@work_bp.route("/tasks/add", methods=["GET", "POST"])
@login_required
@roles_required("admin", "manager")
def task_add():
    projects = Project.query.order_by(Project.name).all()
    employees = Employee.query.order_by(Employee.full_name).all()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if not title:
            flash("Task ka title zaroori hai.", "danger")
        else:
            task = Task(
                title=title,
                description=request.form.get("description", "").strip(),
                status=request.form.get("status", "Pending"),
                priority=request.form.get("priority", "Medium"),
                due_date=parse_date(request.form.get("due_date")),
                project_id=request.form.get("project_id") or None,
                employee_id=request.form.get("employee_id") or None,
            )
            db.session.add(task)
            log_action(f"Task added: {title}")
            db.session.commit()
            flash("Task add ho gaya.", "success")
            return redirect(url_for("work.task_list"))

    return render_template("tasks/form.html", task=None, projects=projects, employees=employees,
                           statuses=TASK_STATUSES, priorities=PRIORITIES)


@work_bp.route("/tasks/<int:task_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required("admin", "manager")
def task_edit(task_id):
    task = db.get_or_404(Task, task_id)
    projects = Project.query.order_by(Project.name).all()
    employees = Employee.query.order_by(Employee.full_name).all()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if not title:
            flash("Task ka title zaroori hai.", "danger")
        else:
            task.title = title
            task.description = request.form.get("description", "").strip()
            task.status = request.form.get("status", "Pending")
            task.priority = request.form.get("priority", "Medium")
            task.due_date = parse_date(request.form.get("due_date"))
            task.project_id = request.form.get("project_id") or None
            task.employee_id = request.form.get("employee_id") or None
            log_action(f"Task updated: {title}")
            db.session.commit()
            flash("Task update ho gaya.", "success")
            return redirect(url_for("work.task_list"))

    return render_template("tasks/form.html", task=task, projects=projects, employees=employees,
                           statuses=TASK_STATUSES, priorities=PRIORITIES)


@work_bp.route("/tasks/<int:task_id>/status", methods=["POST"])
@login_required
def task_status(task_id):
    task = db.get_or_404(Task, task_id)
    if current_user.role == "employee" and task.employee_id != current_user.employee_id:
        abort(403)

    status = request.form.get("status")
    if status in TASK_STATUSES:
        task.status = status
        log_action(f"Task status changed: {task.title} -> {status}")
        db.session.commit()
        flash("Task status update ho gaya.", "success")
    return redirect(url_for("work.task_list"))


@work_bp.route("/tasks/<int:task_id>/delete", methods=["POST"])
@login_required
@roles_required("admin")
def task_delete(task_id):
    task = db.get_or_404(Task, task_id)
    log_action(f"Task deleted: {task.title}")
    db.session.delete(task)
    db.session.commit()
    flash("Task delete ho gaya.", "success")
    return redirect(url_for("work.task_list"))