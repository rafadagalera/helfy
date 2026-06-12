REGISTER = {"email": "ana@helfy.app", "password": "s3nh4-forte", "name": "Ana"}


def test_register_creates_user(client):
    resp = client.post("/auth/register", json=REGISTER)
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "ana@helfy.app"
    assert "password" not in body and "password_hash" not in body


def test_register_duplicate_email_409(client):
    client.post("/auth/register", json=REGISTER)
    resp = client.post("/auth/register", json=REGISTER)
    assert resp.status_code == 409


def test_login_returns_jwt(client):
    client.post("/auth/register", json=REGISTER)
    resp = client.post("/auth/login", json={"email": REGISTER["email"],
                                            "password": REGISTER["password"]})
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"].count(".") == 2


def test_login_wrong_password_401(client):
    client.post("/auth/register", json=REGISTER)
    resp = client.post("/auth/login", json={"email": REGISTER["email"], "password": "errada"})
    assert resp.status_code == 401


def test_protected_route_requires_token(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 401


def test_me_returns_current_user(client):
    client.post("/auth/register", json=REGISTER)
    token = client.post("/auth/login", json={"email": REGISTER["email"],
                                             "password": REGISTER["password"]}).json()["access_token"]
    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == REGISTER["email"]
