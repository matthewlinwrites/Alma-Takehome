import io

from fastapi.testclient import TestClient


def _create_lead(client: TestClient):
    return client.post(
        "/api/leads",
        data={
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane@example.com",
        },
        files={"resume": ("resume.pdf", io.BytesIO(b"fake pdf content"), "application/pdf")},
    )


class TestCreateLead:
    def test_create_lead_success(self, client: TestClient):
        resp = _create_lead(client)
        assert resp.status_code == 201
        data = resp.json()
        assert data["first_name"] == "Jane"
        assert data["last_name"] == "Doe"
        assert data["email"] == "jane@example.com"
        assert data["state"] == "PENDING"
        assert data["resume_path"] is not None

    def test_create_lead_without_resume(self, client: TestClient):
        resp = client.post(
            "/api/leads",
            data={
                "first_name": "John",
                "last_name": "Smith",
                "email": "john@example.com",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["resume_path"] is None

    def test_create_lead_invalid_email(self, client: TestClient):
        resp = client.post(
            "/api/leads",
            data={
                "first_name": "Bad",
                "last_name": "Email",
                "email": "not-an-email",
            },
        )
        assert resp.status_code == 422


class TestListLeads:
    def test_list_leads_requires_auth(self, client: TestClient):
        resp = client.get("/api/leads")
        assert resp.status_code == 403

    def test_list_leads_invalid_key(self, client: TestClient):
        resp = client.get("/api/leads", headers={"X-API-Key": "wrong"})
        assert resp.status_code == 401

    def test_list_leads_success(self, client: TestClient, api_key: str):
        _create_lead(client)
        resp = client.get("/api/leads", headers={"X-API-Key": api_key})
        assert resp.status_code == 200
        assert len(resp.json()) == 1


class TestGetLead:
    def test_get_lead_success(self, client: TestClient, api_key: str):
        lead_id = _create_lead(client).json()["id"]
        resp = client.get(f"/api/leads/{lead_id}", headers={"X-API-Key": api_key})
        assert resp.status_code == 200
        assert resp.json()["id"] == lead_id

    def test_get_lead_not_found(self, client: TestClient, api_key: str):
        resp = client.get("/api/leads/nonexistent", headers={"X-API-Key": api_key})
        assert resp.status_code == 404


class TestUpdateLead:
    def test_update_to_reached_out(self, client: TestClient, api_key: str):
        lead_id = _create_lead(client).json()["id"]
        resp = client.put(
            f"/api/leads/{lead_id}",
            headers={"X-API-Key": api_key},
            json={"state": "REACHED_OUT"},
        )
        assert resp.status_code == 200
        assert resp.json()["state"] == "REACHED_OUT"

    def test_cannot_transition_twice(self, client: TestClient, api_key: str):
        lead_id = _create_lead(client).json()["id"]
        headers = {"X-API-Key": api_key}
        client.put(f"/api/leads/{lead_id}", headers=headers, json={"state": "REACHED_OUT"})
        resp = client.put(f"/api/leads/{lead_id}", headers=headers, json={"state": "REACHED_OUT"})
        assert resp.status_code == 400


class TestDeleteLead:
    def test_soft_delete(self, client: TestClient, api_key: str):
        lead_id = _create_lead(client).json()["id"]
        headers = {"X-API-Key": api_key}

        resp = client.delete(f"/api/leads/{lead_id}", headers=headers)
        assert resp.status_code == 200

        # Should no longer appear in list
        resp = client.get("/api/leads", headers=headers)
        assert len(resp.json()) == 0

        # Should not be found by ID
        resp = client.get(f"/api/leads/{lead_id}", headers=headers)
        assert resp.status_code == 404
