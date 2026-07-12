from __future__ import annotations

from app.models import Company, CompanyVariable
from tests.conftest import login


def test_admin_can_create_update_and_delete_company_variable(client):
    test_client, SessionLocal, _ = client
    login(test_client, "admin@example.com", "change-me")
    with SessionLocal() as db:
        company = Company(name="Acme")
        db.add(company)
        db.commit()
        company_id = company.id

    create_response = test_client.post(
        f"/admin/companies/{company_id}/variables",
        data={
            "label": "AD Groups",
            "field_type": "dropdown",
            "options_text": "Sales\nIT",
            "required": "true",
            "help_text": "Pick one",
            "applies_to": "onboarding",
            "sort_order": "1",
        },
        follow_redirects=False,
    )
    assert create_response.status_code == 303

    with SessionLocal() as db:
        variable = db.query(CompanyVariable).filter_by(company_id=company_id).one()
        variable_id = variable.id
        assert variable.label == "AD Groups"
        assert variable.options == ["Sales", "IT"]

    update_response = test_client.post(
        f"/admin/variables/{variable_id}",
        data={
            "label": "Department",
            "field_type": "text",
            "options_text": "",
            "help_text": "Optional",
            "applies_to": "both",
            "sort_order": "2",
        },
        follow_redirects=False,
    )
    assert update_response.status_code == 303

    with SessionLocal() as db:
        variable = db.get(CompanyVariable, variable_id)
        assert variable.label == "Department"
        assert variable.field_type == "text"

    delete_response = test_client.post(f"/admin/variables/{variable_id}/delete", follow_redirects=False)
    assert delete_response.status_code == 303

    with SessionLocal() as db:
        assert db.get(CompanyVariable, variable_id) is None
