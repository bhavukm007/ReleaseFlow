from datetime import date
from uuid import UUID

from fastapi.testclient import TestClient

from app.models.release import Release
from app.models.user import User
from app.schemas.release import default_steps
from conftest import TestingSession


def test_signup_login_refresh_me_and_logout(client: TestClient) -> None:
    signup = client.post(
        "/auth/signup",
        json={"full_name": "New User", "email": "new@example.com", "password": "StrongPassword123!"},
    )
    assert signup.status_code == 201
    assert signup.json()["user"]["email"] == "new@example.com"
    assert signup.cookies.get("releaseflow_refresh")
    duplicate = client.post(
        "/auth/signup",
        json={"full_name": "Other", "email": "NEW@example.com", "password": "StrongPassword123!"},
    )
    assert duplicate.status_code == 409
    token = signup.json()["access_token"]
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 200
    client.cookies.update(signup.cookies)
    refreshed = client.post("/auth/refresh")
    assert refreshed.status_code == 200
    client.cookies.update(refreshed.cookies)
    assert client.post("/auth/logout").status_code == 204


def test_first_signup_claims_legacy_releases(client: TestClient) -> None:
    legacy_id = UUID("00000000-0000-0000-0000-000000000001")
    with TestingSession() as db:
        db.add(User(
            id=legacy_id,
            full_name="Legacy Release Owner",
            email="legacy@releaseflow.invalid",
            hashed_password="!account-disabled",
        ))
        db.add(Release(
            name="Pre-upgrade release",
            due_date=date(2026, 9, 1),
            steps=default_steps(),
            owner_id=legacy_id,
        ))
        db.commit()
    signup = client.post("/auth/signup", json={
        "full_name": "First Real User",
        "email": "first@example.com",
        "password": "StrongPassword123!",
    })
    token = signup.json()["access_token"]
    releases = client.get("/releases", headers={"Authorization": f"Bearer {token}"}).json()
    assert [item["name"] for item in releases] == ["Pre-upgrade release"]


def test_unauthenticated_and_cross_user_release_access_is_hidden(client: TestClient) -> None:
    release = client.post("/releases", json={"name": "Private", "due_date": "2026-08-20"}).json()
    assert client.get("/releases", headers={"Authorization": ""}).status_code == 401
    other = client.post(
        "/auth/signup",
        json={"full_name": "Other User", "email": "other@example.com", "password": "StrongPassword123!"},
    ).json()
    headers = {"Authorization": f"Bearer {other['access_token']}"}
    assert client.get(f"/releases/{release['id']}", headers=headers).status_code == 404
    assert client.delete(f"/releases/{release['id']}", headers=headers).status_code == 404


def test_dynamic_checklist_crud_and_activity(client: TestClient) -> None:
    release = client.post(
        "/releases",
        json={"name": "Custom", "due_date": "2026-08-20", "checklist_items": ["Design", "Ship"]},
    ).json()
    assert list(release["steps"]) == ["Design", "Ship"]
    updated = client.patch(
        f"/releases/{release['id']}/checklist",
        json={"items": [{"name": "Ship", "completed": True}, {"name": "Verify", "completed": False}]},
    )
    assert updated.status_code == 200
    assert list(updated.json()["steps"]) == ["Ship", "Verify"]
    assert updated.json()["status"] == "ongoing"
    activities = client.get(f"/releases/{release['id']}/activities").json()
    assert any(item["action"] == "checklist_completed" for item in activities)
    assert any(item["action"] == "step_deleted" for item in activities)
    recent = client.get("/activities?limit=5")
    assert recent.status_code == 200
    assert recent.json()[0]["release_id"] == release["id"]

    renamed = client.patch(
        f"/releases/{release['id']}/checklist",
        json={"items": [{"name": "Deploy", "completed": True}, {"name": "Verify", "completed": False}]},
    )
    assert renamed.status_code == 200
    activities = client.get(f"/releases/{release['id']}/activities").json()
    assert any(
        item["action"] == "step_renamed"
        and item["metadata"] == {"from": "Ship", "to": "Deploy"}
        for item in activities
    )


def test_team_invitation_permissions_and_pending_signup(client: TestClient) -> None:
    team = client.post("/teams", json={"name": "Platform"}).json()
    invitation = client.post(
        f"/teams/{team['id']}/invitations",
        json={"email": "future@example.com", "role": "member"},
    )
    assert invitation.json()["status"] == "invitation_pending"
    joined = client.post(
        "/auth/signup",
        json={"full_name": "Future Member", "email": "future@example.com", "password": "StrongPassword123!"},
    ).json()
    member_headers = {"Authorization": f"Bearer {joined['access_token']}"}
    member_teams = client.get("/teams", headers=member_headers).json()
    assert member_teams[0]["role"] == "member"
    team_release = client.post(
        "/releases",
        json={"name": "Team Launch", "due_date": "2026-09-01", "team_id": team["id"]},
    ).json()
    assert client.get(f"/releases/{team_release['id']}", headers=member_headers).status_code == 404
    assert client.get(f"/releases?team_id={team['id']}", headers=member_headers).json() == []
    shared = client.post(
        f"/releases/{team_release['id']}/collaborators",
        json={"email": "future@example.com", "role": "other"},
    )
    assert shared.status_code == 201
    assert client.get(f"/releases/{team_release['id']}", headers=member_headers).status_code == 200
    assert client.delete(f"/releases/{team_release['id']}", headers=member_headers).status_code == 404


def test_release_scoped_roles_enforce_permissions(client: TestClient) -> None:
    admin = client.post("/auth/signup", json={
        "full_name": "Release Admin", "email": "admin@example.com", "password": "StrongPassword123!",
    }).json()
    other = client.post("/auth/signup", json={
        "full_name": "Checklist Editor", "email": "checklist@example.com", "password": "StrongPassword123!",
    }).json()
    outsider = client.post("/auth/signup", json={
        "full_name": "Outsider", "email": "outsider@example.com", "password": "StrongPassword123!",
    }).json()
    release = client.post("/releases", json={
        "name": "Scoped Release",
        "due_date": "2026-09-10",
        "collaborators": [
            {"email": "admin@example.com", "role": "admin"},
            {"email": "checklist@example.com", "role": "other"},
        ],
    }).json()
    admin_headers = {"Authorization": f"Bearer {admin['access_token']}"}
    other_headers = {"Authorization": f"Bearer {other['access_token']}"}
    outsider_headers = {"Authorization": f"Bearer {outsider['access_token']}"}

    assert client.get(f"/releases/{release['id']}", headers=outsider_headers).status_code == 404
    assert client.get("/releases", headers=outsider_headers).json() == []
    assert client.get(f"/releases/{release['id']}", headers=admin_headers).json()["access_role"] == "admin"
    assert client.patch(
        f"/releases/{release['id']}/info",
        headers=admin_headers,
        json={"additional_info": "Admin can edit notes"},
    ).status_code == 200
    assert client.delete(f"/releases/{release['id']}", headers=admin_headers).status_code == 404
    assert client.post(
        f"/releases/{release['id']}/collaborators",
        headers=admin_headers,
        json={"email": "outsider@example.com", "role": "other"},
    ).status_code == 201

    assert client.patch(
        f"/releases/{release['id']}/info",
        headers=other_headers,
        json={"additional_info": "Not allowed"},
    ).status_code == 404
    checklist = client.patch(
        f"/releases/{release['id']}/checklist",
        headers=other_headers,
        json={"items": [{"name": "New checklist item", "completed": True}]},
    )
    assert checklist.status_code == 200
    assert checklist.json()["steps"] == {"New checklist item": True}
    assert client.delete(f"/releases/{release['id']}", headers=other_headers).status_code == 404

    assert client.delete(f"/releases/{release['id']}").status_code == 204


def test_realtime_websocket_authentication(client: TestClient) -> None:
    login = client.post("/auth/login", json={"email": "test@example.com", "password": "TestPassword123!"}).json()
    with client.websocket_connect(f"/ws?token={login['access_token']}") as socket:
        socket.send_text("ping")
