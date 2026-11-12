# TechNova - IT Company Enterprise Management System

A role-based web application to manage employees, clients, projects, tasks and IT assets of an IT company. Built with Flask and SQLAlchemy.

## Features

- Login / logout with hashed passwords
- Three roles: **Admin**, **Manager**, **Employee** (role-based permissions)
- Dashboard with live statistics from the database
- Employees and Departments (add, edit, delete, search)
- Clients, Projects (with team members) and Tasks (status tracking)
- IT Assets (assign laptops and equipment to employees)
- User management, Reports and Audit Logs (admin only)
- Custom 403 / 404 / 500 error pages

## Role Permissions

| Module | Admin | Manager | Employee |
|---|---|---|---|
| Dashboard | Yes | Yes | Yes |
| Employees / Departments | Full | Add, edit | No |
| Clients / Projects | Full | Add, edit | No |
| Tasks | Full | Add, edit | Own tasks only (update status) |
| IT Assets | Full | Add, edit | No |
| Users / Reports / Audit Logs | Yes | No | No |

## Tech Stack

- Python, Flask
- Flask-SQLAlchemy (ORM), Flask-Login, Flask-Migrate
- SQLite (PostgreSQL-ready through `DATABASE_URL`)
- HTML (Jinja2), CSS, a little JavaScript

## Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python seed.py
python seed_demo.py
python run.py
```

Open http://127.0.0.1:5000

Create a `.env` file:

```
SECRET_KEY=your-own-secret-key
```

Default admin (change the password after the first login): `admin` / `admin123`

## Project Structure

```
TechNova
├── app
│   ├── admin        (users, reports, audit logs)
│   ├── assets
│   ├── auth
│   ├── employees    (employees and departments)
│   ├── work         (clients, projects, tasks)
│   ├── static
│   ├── templates
│   ├── decorators.py
│   └── models.py
├── config.py
├── run.py
├── seed.py
└── seed_demo.py
```

## Database Tables

users, departments, employees, clients, projects, project_members, tasks, assets, audit_logs

## Author

Eiman Shakoor - BS Information Technology, KFUEIT