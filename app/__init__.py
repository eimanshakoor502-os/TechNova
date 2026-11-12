from datetime import date
from flask import Flask, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, current_user
from flask_migrate import Migrate
from sqlalchemy import func
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = "auth.login"

TASK_LABELS = ["Pending", "In Progress", "Done"]
PROJECT_LABELS = ["Active", "On Hold", "Completed"]
ASSET_LABELS = ["Available", "Assigned", "Repair"]


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from app import models  # noqa: F401
    from app.auth.routes import auth_bp
    from app.employees.routes import employees_bp
    from app.work.routes import work_bp
    from app.assets.routes import assets_bp
    from app.admin.routes import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(work_bp)
    app.register_blueprint(assets_bp)
    app.register_blueprint(admin_bp)

    @app.route("/")
    def home():
        return redirect(url_for("dashboard"))

    @app.route("/dashboard")
    @login_required
    def dashboard():
        from app.models import Employee, Client, Project, Task, Asset, AuditLog, Department

        today = date.today()

        # ---------- EMPLOYEE: sirf apne tasks ----------
        if current_user.role == "employee":
            emp_id = current_user.employee_id
            tasks = Task.query.filter_by(employee_id=emp_id).all() if emp_id else []

            counts = {s: 0 for s in TASK_LABELS}
            for t in tasks:
                counts[t.status] = counts.get(t.status, 0) + 1
            overdue = sum(1 for t in tasks if t.due_date and t.due_date < today and t.status != "Done")

            cards = [
                {"num": len(tasks), "label": "My Tasks"},
                {"num": counts["Pending"], "label": "Pending"},
                {"num": counts["In Progress"], "label": "In Progress"},
                {"num": counts["Done"], "label": "Done"},
                {"num": overdue, "label": "Overdue"},
            ]
            open_tasks = [t for t in tasks if t.status != "Done"]
            open_tasks.sort(key=lambda t: (t.due_date is None, t.due_date or today))

            charts = {"tasks": {"labels": TASK_LABELS, "values": [counts[s] for s in TASK_LABELS]}}
            return render_template("dashboard.html", cards=cards, charts=charts,
                                   my_tasks=open_tasks[:5], linked=bool(emp_id), today=today)

        # ---------- ADMIN / MANAGER: company dashboard ----------
        overdue = Task.query.filter(Task.due_date < today, Task.status != "Done").count()
        cards = [
            {"num": Employee.query.count(), "label": "Employees"},
            {"num": Client.query.count(), "label": "Clients"},
            {"num": Project.query.filter_by(status="Active").count(), "label": "Active Projects"},
            {"num": Task.query.filter(Task.status != "Done").count(), "label": "Pending Tasks"},
            {"num": Asset.query.count(), "label": "IT Assets"},
            {"num": overdue, "label": "Overdue Tasks"},
        ]

        task_counts = dict(db.session.query(Task.status, func.count(Task.id)).group_by(Task.status).all())
        project_counts = dict(db.session.query(Project.status, func.count(Project.id)).group_by(Project.status).all())
        asset_counts = dict(db.session.query(Asset.status, func.count(Asset.id)).group_by(Asset.status).all())
        dept_rows = (
            db.session.query(Department.name, func.count(Employee.id))
            .outerjoin(Employee, Employee.department_id == Department.id)
            .group_by(Department.name)
            .order_by(Department.name)
            .all()
        )

        charts = {
            "tasks": {"labels": TASK_LABELS, "values": [task_counts.get(s, 0) for s in TASK_LABELS]},
            "projects": {"labels": PROJECT_LABELS, "values": [project_counts.get(s, 0) for s in PROJECT_LABELS]},
            "assets": {"labels": ASSET_LABELS, "values": [asset_counts.get(s, 0) for s in ASSET_LABELS]},
            "departments": {"labels": [r[0] for r in dept_rows], "values": [r[1] for r in dept_rows]},
        }

        upcoming_projects = (
            Project.query.filter(Project.status == "Active", Project.deadline.isnot(None))
            .order_by(Project.deadline).limit(5).all()
        )
        recent_logs = []
        if current_user.role == "admin":
            recent_logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(8).all()

        return render_template("dashboard.html", cards=cards, charts=charts,
                               upcoming_projects=upcoming_projects, recent_logs=recent_logs, today=today)

    @app.errorhandler(401)
    def unauthorized(e):
        return redirect(url_for("auth.login"))

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("error.html", code=403,
                               message="Aap ko is page ka access nahi hai."), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("error.html", code=404,
                               message="Ye page maujood nahi hai."), 404

    @app.errorhandler(500)
    def server_error(e):
        db.session.rollback()
        return render_template("error.html", code=500,
                               message="Kuch masla aa gaya. Dobara koshish karo."), 500

    return app