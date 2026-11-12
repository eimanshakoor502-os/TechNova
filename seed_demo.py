from datetime import date, timedelta
from app import create_app, db
from app.models import Department, Employee, Client, Project, Task, Asset

app = create_app()

with app.app_context():
    if Employee.query.count() > 0:
        print("Demo data pehle se maujood hai.")
    else:
        dev = Department.query.filter_by(name="Development").first()
        design = Department.query.filter_by(name="Design").first()

        e1 = Employee(full_name="Ali Raza", email="ali@technova.com", designation="Backend Developer", department_id=dev.id)
        e2 = Employee(full_name="Sara Khan", email="sara@technova.com", designation="UI Designer", department_id=design.id)
        e3 = Employee(full_name="Usman Tariq", email="usman@technova.com", designation="Frontend Developer", department_id=dev.id)
        db.session.add_all([e1, e2, e3])

        c1 = Client(company_name="Alpha Traders", contact_person="Hamza", email="hamza@alpha.com")
        c2 = Client(company_name="Beta Logistics", contact_person="Nida", email="nida@beta.com")
        db.session.add_all([c1, c2])
        db.session.flush()

        p1 = Project(name="E-commerce Website", client_id=c1.id, status="Active", deadline=date.today() + timedelta(days=30))
        p2 = Project(name="Fleet Tracking App", client_id=c2.id, status="Active", deadline=date.today() + timedelta(days=60))
        db.session.add_all([p1, p2])
        db.session.flush()

        db.session.add_all([
            Task(title="Login API banana", project_id=p1.id, employee_id=e1.id, status="In Progress"),
            Task(title="Homepage design", project_id=p1.id, employee_id=e2.id, status="Pending"),
            Task(title="Map screen", project_id=p2.id, employee_id=e3.id, status="Pending"),
            Task(title="Database design", project_id=p2.id, employee_id=e1.id, status="Done"),
        ])

        db.session.add_all([
            Asset(name="Dell Latitude 5420", asset_type="Laptop", serial_number="DL-1001", status="Assigned", employee_id=e1.id),
            Asset(name="HP ProBook 450", asset_type="Laptop", serial_number="HP-2002", status="Available"),
        ])

        db.session.commit()
        print("Demo data add ho gaya.")