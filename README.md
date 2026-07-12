# Roster Hub

Roster Hub is a standalone multi-tenant onboarding and offboarding portal for MSP use.
It lets administrators manage companies, contact users, company-specific request variables, SMTP settings, and language packs.
Client contacts sign in to their own company portal, start onboarding or offboarding requests, fill in company-specific variables, and trigger an email notification.

## Features

- FastAPI backend with server-rendered dashboard UI
- PostgreSQL storage
- Docker Compose deployment
- Seeded initial admin user on first run
- Multi-tenant roles: `admin` and `client_contact`
- Per-company variable configuration
- Onboarding and offboarding request submission
- Email notification on request submission
- Editable language packs with shipped EN and DE baselines
- Light and dark theme support

## Repository layout

```text
app/                FastAPI app, templates, static files, built-in language files
migrations/         Initial SQL schema snapshot
tests/              Pytest suite
docs/               Architecture notes
Dockerfile
docker-compose.yml
.env.example
README.md
```

## Run locally with Docker Compose

```sh
cp .env.example .env
docker compose up --build
```

Open:

```text
http://localhost:8084
```

The first admin account is seeded from `.env`:

```text
INITIAL_ADMIN_EMAIL=admin@example.com
INITIAL_ADMIN_PASSWORD=change-me
```

## Environment variables

| Variable | Description | Default |
| --- | --- | --- |
| `APP_NAME` | Application name | `Roster Hub` |
| `APP_ENV` | Runtime environment | `development` |
| `PUBLIC_URL` | External URL for documentation/login context | `http://localhost:8084` |
| `DATABASE_URL` | SQLAlchemy database URL | `postgresql+psycopg://rosterhub:rosterhub@roster-hub-db:5432/rosterhub` |
| `SECRET_KEY` | Session token HMAC secret | `change-me` |
| `SESSION_COOKIE_NAME` | Session cookie name | `roster_hub_session` |
| `SESSION_SECURE` | Mark session cookies secure | `false` |
| `SESSION_TTL_HOURS` | Session duration | `12` |
| `INITIAL_ADMIN_EMAIL` | Seed admin email | `admin@example.com` |
| `INITIAL_ADMIN_PASSWORD` | Seed admin password | `change-me` |
| `DEFAULT_LANGUAGE` | Fallback language code | `EN` |
| `LANGUAGE_STORAGE_DIR` | Persistent directory for installed language files | `/var/lib/roster-hub/languages` |
| `SMTP_ENABLED` | Seed SMTP enabled state | `false` |
| `SMTP_HOST` | Seed SMTP host | empty |
| `SMTP_PORT` | Seed SMTP port | `587` |
| `SMTP_USERNAME` | Seed SMTP username | empty |
| `SMTP_PASSWORD` | Seed SMTP password | empty |
| `SMTP_FROM_ADDRESS` | Seed sender address | empty |
| `SMTP_FROM_NAME` | Seed sender display name | `Roster Hub` |
| `SMTP_USE_TLS` | Seed STARTTLS preference | `true` |
| `SMTP_USE_SSL` | Seed SSL/TLS preference | `false` |

## Adding a new language

1. Sign in as an admin.
2. Open **Languages**.
3. Download the language template.
4. Set `LANG` to a new code such as `ES`.
5. Set `DISPLAY_NAME` to the language label shown in the dropdown.
6. Translate every string in `STRINGS`.
7. Upload the JSON file in the admin UI.

Validation rules in v1:

- only JSON uploads are accepted
- required translation keys must all be present
- invalid `LANG` values are rejected
- untranslated or blank keys are reported back as warnings

After upload, the new language appears automatically in the language selector.

## Test suite

Install dependencies locally and run:

```sh
python -m pip install -r requirements.txt
pytest
```

## Known limitations

- No MFA in v1
- No automated onboarding/offboarding execution yet
- No self-service company signup
- No integration with OPNsense-Hub or M365-Toolbox
