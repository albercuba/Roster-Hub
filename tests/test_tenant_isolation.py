from __future__ import annotations

from datetime import date

from app.models import Company, Request, User
from app.security import hash_password
from tests.conftest import login


def test_client_contact_cannot_view_other_company_request(client):
    test_client, SessionLocal, _ = client
    with SessionLocal() as db:
        company_a = Company(name="Alpha")
        company_b = Company(name="Beta")
        db.add_all([company_a, company_b])
        db.flush()
        user_a = User(email="a@example.com", password_hash=hash_password("pass123"), role="client_contact", company_id=company_a.id)
        user_b = User(email="b@example.com", password_hash=hash_password("pass123"), role="client_contact", company_id=company_b.id)
        db.add_all([user_a, user_b])
        db.flush()
        request_a = Request(company_id=company_a.id, created_by_user_id=user_a.id, process_type="onboarding", employee_name="Alice", relevant_date=date(2026, 1, 1), status="submitted")
        request_b = Request(company_id=company_b.id, created_by_user_id=user_b.id, process_type="offboarding", employee_name="Bob", relevant_date=date(2026, 1, 2), status="submitted")
        db.add_all([request_a, request_b])
        db.commit()
        request_a_id = request_a.id
        request_b_id = request_b.id

    response = login(test_client, "a@example.com", "pass123")
    assert response.status_code == 303

    own_response = test_client.get(f"/portal/requests/{request_a_id}")
    assert own_response.status_code == 200
    other_response = test_client.get(f"/portal/requests/{request_b_id}")
    assert other_response.status_code == 404
