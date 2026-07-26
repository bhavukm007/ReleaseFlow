from fastapi.testclient import TestClient

from app.schemas.release import DEFAULT_STEP_NAMES


def create_release(client: TestClient) -> dict:
    response = client.post("/releases", json={"name": "API Launch", "due_date": "2026-08-15", "additional_info": "Watch metrics"})
    assert response.status_code == 201
    return response.json()


def test_create_release_has_default_steps_and_planned_status(client: TestClient) -> None:
    release = create_release(client)
    assert release["status"] == "planned"
    assert release["completed_steps"] == 0
    assert release["steps"] == {name: False for name in DEFAULT_STEP_NAMES}


def test_updating_steps_computes_done_status(client: TestClient) -> None:
    release = create_release(client)
    response = client.patch(f"/releases/{release['id']}/steps", json={"steps": {name: True for name in DEFAULT_STEP_NAMES}})
    assert response.status_code == 200
    assert response.json()["status"] == "done"
    assert response.json()["completed_steps"] == 8


def test_info_update_and_delete_lifecycle(client: TestClient) -> None:
    release = create_release(client)
    response = client.patch(f"/releases/{release['id']}/info", json={"additional_info": "Updated notes"})
    assert response.json()["additional_info"] == "Updated notes"
    assert client.delete(f"/releases/{release['id']}").status_code == 204
    assert client.get(f"/releases/{release['id']}").status_code == 404


def test_rejects_invalid_step_shape(client: TestClient) -> None:
    release = create_release(client)
    response = client.patch(f"/releases/{release['id']}/steps", json={"steps": {"Code Freeze": True}})
    assert response.status_code == 422
