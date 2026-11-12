from app import create_app, db
from app.models import User, Department

app = create_app()

with app.app_context():
    db.create_all()

    if not User.query.filter_by(username="admin").first():
        admin = User(username="admin", email="admin@technova.com", role="admin")
        admin.set_password("admin123")
        db.session.add(admin)

    for name in ["Development", "Design", "QA", "HR", "IT Support"]:
        if not Department.query.filter_by(name=name).first():
            db.session.add(Department(name=name))

    db.session.commit()
    print("Database tayyar hai. Admin user: admin / admin123")