# Roster Hub architecture

## Overview

Roster Hub is a standalone FastAPI application for collecting multi-tenant onboarding and offboarding requests.
It uses server-rendered Jinja templates, PostgreSQL for persistence, and SMTP for outbound request notifications.

## Major components

- `app/main.py` — FastAPI app, lifespan bootstrap, static mounting, and security headers.
- `app/models.py` — SQLAlchemy models for companies, users, variables, requests, variable values, sessions, email settings, and audit entries.
- `app/routers/auth.py` — login, logout, theme switching, and language switching.
- `app/routers/admin.py` — admin CRUD for companies, users, variables, requests, email settings, and language files.
- `app/routers/client.py` — client-contact request submission and request history.
- `app/services/language_service.py` — language discovery, upload validation, and template generation.
- `app/services/mail_service.py` — SMTP delivery for request notifications.
- `app/services/bootstrap.py` — schema creation, language seeding, and initial admin seeding.

## Tenant isolation

- `admin` users can view and manage all companies, variables, users, and requests.
- `client_contact` users are scoped to their assigned `company_id`.
- Client request access is enforced server-side in `app/deps.py::ensure_request_access`.

## Language model

Language files are JSON documents stored in a persistent language directory. Each file contains:

- `LANG` — ISO 639-1 style uppercase code, optionally with a region suffix
- `DISPLAY_NAME` — label shown in the selector
- `STRINGS` — flat key/value map

Uploaded files are validated against the required v1 key set before they are stored.

## Email delivery

Request submission sends an SMTP email to the notification address configured on the target company record.
SMTP defaults can be seeded from environment variables and then edited in the admin UI.

## Known v1 limitations

- No MFA
- No workflow automation beyond saving the request and sending a notification email
- No background job queue
- No integration with M365-Toolbox or OPNsense-Hub
