from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Asset, Employee, AuditLog
from app.decorators import roles_required

assets_bp = Blueprint("assets", __name__)

ASSET_TYPES = ["Laptop", "Desktop", "Monitor", "Phone", "Tablet", "Printer", "Router", "Other"]
ASSET_STATUSES = ["Available", "Assigned", "Repair"]


def log_action(text):
    db.session.add(AuditLog(user_id=current_user.id, action=text))


def parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def fill_asset(asset):
    """Form ka data asset mein bharta hai. Error ho to message wapas deta hai."""
    name = request.form.get("name", "").strip()
    if not name:
        return "Asset ka naam zaroori hai."

    serial = request.form.get("serial_number", "").strip() or None
    if serial:
        other = Asset.query.filter(Asset.serial_number == serial, Asset.id != (asset.id or 0)).first()
        if other:
            return "Ye serial number pehle se maujood hai."

    employee_id = request.form.get("employee_id") or None
    status = request.form.get("status", "Available")

    # Employee chuna hai to status Assigned, warna Assigned nahi ho sakta
    if employee_id and status == "Available":
        status = "Assigned"
    if not employee_id and status == "Assigned":
        status = "Available"

    asset.name = name
    asset.asset_type = request.form.get("asset_type", "Other")
    asset.serial_number = serial
    asset.status = status
    asset.purchase_date = parse_date(request.form.get("purchase_date"))
    asset.employee_id = employee_id
    return None


@assets_bp.route("/assets")
@login_required
@roles_required("admin", "manager")
def asset_list():
    items = Asset.query.order_by(Asset.name).all()
    return render_template("assets/list.html", assets=items)


@assets_bp.route("/assets/add", methods=["GET", "POST"])
@login_required
@roles_required("admin", "manager")
def asset_add():
    employees = Employee.query.order_by(Employee.full_name).all()

    if request.method == "POST":
        asset = Asset()
        error = fill_asset(asset)
        if error:
            flash(error, "danger")
        else:
            db.session.add(asset)
            log_action(f"Asset added: {asset.name}")
            db.session.commit()
            flash("Asset add ho gaya.", "success")
            return redirect(url_for("assets.asset_list"))

    return render_template("assets/form.html", asset=None, employees=employees,
                           types=ASSET_TYPES, statuses=ASSET_STATUSES)


@assets_bp.route("/assets/<int:asset_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required("admin", "manager")
def asset_edit(asset_id):
    asset = db.get_or_404(Asset, asset_id)
    employees = Employee.query.order_by(Employee.full_name).all()

    if request.method == "POST":
        error = fill_asset(asset)
        if error:
            db.session.rollback()
            flash(error, "danger")
        else:
            log_action(f"Asset updated: {asset.name}")
            db.session.commit()
            flash("Asset update ho gaya.", "success")
            return redirect(url_for("assets.asset_list"))

    return render_template("assets/form.html", asset=asset, employees=employees,
                           types=ASSET_TYPES, statuses=ASSET_STATUSES)


@assets_bp.route("/assets/<int:asset_id>/delete", methods=["POST"])
@login_required
@roles_required("admin")
def asset_delete(asset_id):
    asset = db.get_or_404(Asset, asset_id)
    log_action(f"Asset deleted: {asset.name}")
    db.session.delete(asset)
    db.session.commit()
    flash("Asset delete ho gaya.", "success")
    return redirect(url_for("assets.asset_list"))