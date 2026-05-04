def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


def test_create_client(client):
    r = client.post(
        "/clients",
        json={
            "name": "Тест Клиент",
            "email": "test@example.com",
            "phone": "+79001234567",
            "company": "ООО Тест",
            "status": "active",
        },
    )
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Тест Клиент"


def test_list_clients_pagination(client):
    client.post("/clients", json={"name": "A", "status": "active"})
    r = client.get("/clients", params={"skip": 0, "limit": 10})
    assert r.status_code == 200
    body = r.json()
    assert "total" in body and "items" in body


def test_unknown_client_returns_422_or_404_on_patch(client):
    r = client.patch("/clients/99999", json={"name": "noop"})
    assert r.status_code in (404, 422)
