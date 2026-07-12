from __future__ import annotations

from app.models import Company, CompanyVariable, Request, RequestVariableValue, User
from app.security import hash_password
from tests.conftest import login


def test_start_onboarding_page_renders_form(client):
    test_client, SessionLocal, _ = client
    with SessionLocal() as db:
        company = Company(name="Acme", notification_email="it@acme.example")
        db.add(company)
        db.flush()
        user = User(email="contact@acme.example", password_hash=hash_password("pass123"), role="client_contact", company_id=company.id)
        db.add(user)
        db.commit()

    login(test_client, "contact@acme.example", "pass123")
    response = test_client.get("/portal/requests/new?process_type=onboarding")

    assert response.status_code == 200
    assert "Start onboarding" in response.text
    assert "employee_name" in response.text


def test_request_submission_saves_request_and_triggers_email(client, monkeypatch):
    test_client, SessionLocal, _ = client
    with SessionLocal() as db:
        company = Company(name="Acme", notification_email="it@acme.example")
        db.add(company)
        db.flush()
        user = User(email="contact@acme.example", password_hash=hash_password("pass123"), role="client_contact", company_id=company.id)
        variable = CompanyVariable(company_id=company.id, label="Department", field_type="text", required=True, applies_to="both", sort_order=1)
        db.add_all([user, variable])
        db.commit()
        variable_id = variable.id

    sent = {"called": False}

    def fake_send_email(db, request_record):
        sent["called"] = True
        return True

    monkeypatch.setattr("app.routers.client.send_request_notification_email", fake_send_email)
    login(test_client, "contact@acme.example", "pass123")
    response = test_client.post(
        "/portal/requests",
        data={
            "process_type": "onboarding",
            "employee_name": "Alice Example",
            "relevant_date": "2026-01-10",
            "notes": "Prepare laptop",
            f"variable_{variable_id}": "Engineering",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert sent["called"] is True

    with SessionLocal() as db:
        request_record = db.query(Request).one()
        assert request_record.employee_name == "Alice Example"
        value = db.query(RequestVariableValue).one()
        assert value.value == "Engineering"
