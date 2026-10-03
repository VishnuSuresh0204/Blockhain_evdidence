# Blockchain Evidence

A Django application for registering users, uploading digital evidence, checking
for duplicate or visually similar images, and recording evidence verification
and administrator review activity.

The application stores blockchain-style evidence records in its Django database;
it does not connect to a public or decentralized blockchain network.

## Features

- User registration, login, profile editing, and profile images.
- Evidence uploads with SHA-256 hashes for exact duplicate detection.
- Perceptual-hash and ORB comparisons to flag potentially modified or similar
  images.
- Verification history and blockchain-style evidence records.
- Admin dashboards for reviewing evidence, alerts, users, and verification
  activity.

## Requirements

- Python 3.11 or newer.
- Django 5.2.
- Pillow, ImageHash, OpenCV, and NumPy for image processing and similarity
  checks.

## Run locally on Windows

Open PowerShell in the project directory (the folder containing `manage.py`):

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install "Django>=5.2,<5.3" Pillow ImageHash opencv-python numpy
python manage.py migrate
python manage.py runserver
```

Open <http://127.0.0.1:8000/> in a browser. The Django admin is available at
<http://127.0.0.1:8000/admin/>.

To use Django's development server with a generated secret key in the current
PowerShell session:

```powershell
$env:DJANGO_SECRET_KEY = python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Run this before starting the server. The SQLite database is created locally as
`db.sqlite3`; apply future schema changes with `python manage.py migrate`.

## Project layout

- `evid/` — Django project settings and URL configuration.
- `myapp/` — user, evidence, blockchain-record, verification, and alert models
  and application views.
- `myapp/migrations/` — database schema migrations.
- `templates/` — shared, user, and admin pages.
- `static/` — application CSS.
- `media/` — uploaded evidence and profile files stored locally at runtime.

The repository includes four DOCX evidence test fixtures. Other local media
uploads, including profile images and evidence images, are not part of the
repository.

## Security

The checked-in Django configuration is for local development, not production.
Before deployment, configure a private `DJANGO_SECRET_KEY`, set `DEBUG = False`,
restrict `ALLOWED_HOSTS`, and configure secure HTTPS, static-file, and
user-upload handling.

The current account model also has a separate `view_pass` field populated during
registration. Review and remove any plaintext-password storage before using the
application with real accounts; Django's hashed password field should be the
only stored password.
