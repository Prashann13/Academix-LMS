# Academix

A role-based Learning Management System built with Django — separate dashboards and permissions for **Administrators**, **Lecturers**, and **Students**.

Stack: Python 3.10+ · Django 5.0+ · SQLite · Django templates · Bootstrap 5 · vanilla JavaScript

## Quick start

```bash
python -m venv venv
venv\Scripts\activate            # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo_data  # optional demo data
python manage.py runserver
```

Visit `http://127.0.0.1:8000/`. Demo logins after seeding:

| Username    | Password           | Role     |
|-------------|--------------------|----------|
| `admin`     | `AdminPass123!`    | Admin    |
| `lecturer1` | `LecturerPass123!` | Lecturer |
| `student1`  | `StudentPass123!`  | Student  |

## Features

- **Roles** — custom `accounts.User` with a `role` field, enforced by a
  `role_required` decorator and a `RoleRequiredMixin` for class-based views.
- **Academics** — sessions, semesters, programs, courses, lecturer allocations,
  student records with automatic grading, and news/events. Full CRUD throughout.
- **Bulk CSV import** — 500+ students in a handful of queries, with a preview, a
  per-row report, and idempotent re-runs. Web page and `--dry-run` CLI over one
  engine in `students/services.py`.
- **UI** — Bootstrap 5 reskinned via CSS custom properties, off-canvas sidebar,
  live table search and sort, no frontend framework.

## Role permissions

| Action                              | Admin | Lecturer | Student |
|--------------------------------------|:-----:|:--------:|:-------:|
| Manage sessions/semesters            |  Yes  |    No    |   No    |
| Manage programs/courses/allocations  |  Yes  |    No    |   No    |
| View courses/programs                |  Yes  |   Yes    |   Yes   |
| Create/manage user accounts          |  Yes  |    No    |   No    |
| View student list                    |  Yes  |   Yes    |   No    |
| Enter/edit grades                    |  Yes  |   Yes    |   No    |
| View own grades                      |  Yes  |   Yes    |   Yes   |
| Bulk-import students from CSV        |  Yes  |    No    |   No    |
| Post news/events                     |  Yes  |    No    |   No    |
| View news/events                     |  Yes  |   Yes    |   Yes   |

## Bulk import

**Web:** admin → **Import Students**. **CLI:** `python manage.py import_students --file students.csv` (`--dry-run` validates only, `--update` refreshes duplicates).

CSV columns: `username,first_name,last_name,email,phone_number,program,level,date_of_birth,address`

## Configuration

Copy `.env.example` to `.env`; every variable is documented there.
`DJANGO_SECRET_KEY` is required in production and `DJANGO_DEBUG` must be `False`.
Deploying needs `collectstatic` plus WhiteNoise to serve `STATIC_ROOT`.

## Tests

`python manage.py test` — 46 tests: role decorator and mixin, import engine validation and idempotency, both import entry points, and `--dry-run`.

Licence: not yet specified.
