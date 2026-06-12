def auth_headers(client, email="user@helfy.app", password="s3nh4-forte", name="User"):
    """Registra (se preciso), loga e retorna (headers, user_id)."""
    reg = client.post("/auth/register",
                      json={"email": email, "password": password, "name": name})
    user_id = reg.json().get("id")
    token = client.post("/auth/login",
                        json={"email": email, "password": password}).json()["access_token"]
    if user_id is None:  # usuário já existia; descobre o id via /auth/me
        me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        user_id = me.json()["id"]
    return {"Authorization": f"Bearer {token}"}, user_id
