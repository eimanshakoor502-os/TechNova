from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, AuditLog

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()

        if user and user.is_active_user and user.check_password(password):
            login_user(user)
            db.session.add(AuditLog(user_id=user.id, action="Logged in"))
            db.session.commit()
            return redirect(url_for("dashboard"))

        flash("Username ya password galat hai.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    db.session.add(AuditLog(user_id=current_user.id, action="Logged out"))
    db.session.commit()
    logout_user()
    return redirect(url_for("auth.login"))