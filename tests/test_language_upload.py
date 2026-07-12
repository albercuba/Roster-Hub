from __future__ import annotations

import json
from pathlib import Path

from tests.conftest import login


def test_language_upload_validation_and_success(client):
    test_client, SessionLocal, language_dir = client
    login(test_client, "admin@example.com", "change-me")

    invalid_payload = {"LANG": "ES", "DISPLAY_NAME": "Español", "STRINGS": {"app.name": "Roster Hub"}}
    invalid_response = test_client.post(
        "/admin/languages/upload",
        files={"language_file": ("ES.json", json.dumps(invalid_payload).encode("utf-8"), "application/json")},
    )
    assert invalid_response.status_code == 400
    assert "Missing required keys" in invalid_response.text

    english = json.loads(Path("app/lang/EN.json").read_text(encoding="utf-8"))
    english["LANG"] = "ES"
    english["DISPLAY_NAME"] = "Español"
    english["STRINGS"]["auth.title"] = "Iniciar sesión"
    valid_response = test_client.post(
        "/admin/languages/upload",
        files={"language_file": ("ES.json", json.dumps(english).encode("utf-8"), "application/json")},
        follow_redirects=False,
    )
    assert valid_response.status_code == 303

    languages_page = test_client.get("/admin/languages")
    assert languages_page.status_code == 200
    assert "Español" in languages_page.text
    assert (language_dir / "ES.json").exists()
