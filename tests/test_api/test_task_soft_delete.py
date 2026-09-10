from datetime import UTC, datetime, timedelta

import pytest

from app.models import Tasks
from app.schemas import TaskResponse


@pytest.mark.parametrize("status", ["pending", "in_progress", "done"])
@pytest.mark.parametrize("optional_fields", [False, True])
def test_delete_and_restore_should_preserve_task_and_allow_further_updates(
    test_client, test_session, auth_headers_first_user, status, optional_fields
):
    payload = {"name": "Recover me", "priority": "high", "status": status}
    if optional_fields:
        payload.update(
            description="Original description",
            due_date=(datetime.now(UTC) + timedelta(days=7)).isoformat(),
        )
    created = test_client.post("/api/v1/tasks", headers=auth_headers_first_user, json=payload)
    assert created.status_code == 201
    original = created.json()
    task_id = original["id"]
    url = f"/api/v1/tasks/{task_id}"
    assert test_session.get(Tasks, task_id).is_deleted is False

    deleted = test_client.delete(url, headers=auth_headers_first_user)
    assert deleted.status_code == 204
    assert deleted.content == b""
    test_session.expire_all()
    stored = test_session.get(Tasks, task_id)
    assert stored is not None
    assert stored.is_deleted is True
    assert TaskResponse.model_validate(stored).model_dump(mode="json") == original

    restored = test_client.post(f"{url}/restore", headers=auth_headers_first_user)
    assert restored.status_code == 200
    assert restored.json() == original
    test_session.expire_all()
    assert test_session.get(Tasks, task_id).is_deleted is False
    assert test_client.get(url, headers=auth_headers_first_user).json() == original
    assert test_client.get("/api/v1/tasks", headers=auth_headers_first_user).json() == [original]
    stats = test_client.get("/api/v1/tasks/stats", headers=auth_headers_first_user)
    assert stats.json() == {"completed_count": int(status == "done"), "total_tasks": 1}

    patched = test_client.patch(url, headers=auth_headers_first_user, json={"name": "Recovered"})
    assert patched.status_code == 200
    assert patched.json() == {**original, "name": "Recovered"}
    assert test_client.delete(url, headers=auth_headers_first_user).status_code == 204
    restored_again = test_client.post(f"{url}/restore", headers=auth_headers_first_user)
    assert restored_again.status_code == 200
    assert restored_again.json() == patched.json()


@pytest.mark.parametrize(
    ("method", "kwargs"),
    [
        ("get", {}),
        ("patch", {"json": {}}),
        ("patch", {"json": {"name": "Changed"}}),
        ("delete", {}),
    ],
)
def test_deleted_task_should_return_404_and_remain_unchanged(
    test_client, auth_headers_first_user, test_task, method, kwargs
):
    task_id = test_task["id"]
    url = f"/api/v1/tasks/{task_id}"
    assert test_client.delete(url, headers=auth_headers_first_user).status_code == 204
    response = test_client.request(method, url, headers=auth_headers_first_user, **kwargs)
    assert response.status_code == 404
    assert response.json() == {"detail": f"Task {task_id} not found"}
    assert test_client.get("/api/v1/tasks", headers=auth_headers_first_user).json() == []
    assert test_client.get("/api/v1/tasks/stats", headers=auth_headers_first_user).json() == {
        "completed_count": 0,
        "total_tasks": 0,
    }
    restored = test_client.post(f"{url}/restore", headers=auth_headers_first_user)
    assert restored.status_code == 200
    assert restored.json() == test_task


@pytest.mark.parametrize("deleted", [False, True])
@pytest.mark.parametrize(
    ("method", "suffix", "kwargs"),
    [
        ("delete", "", {}),
        ("post", "/restore", {}),
        ("get", "", {}),
        ("patch", "", {"json": {}}),
        ("patch", "", {"json": {"name": "Intrusion"}}),
    ],
)
def test_foreign_task_should_return_404_without_changing_owner_data(
    test_client,
    test_session,
    auth_headers_first_user,
    auth_headers_second_user,
    test_task,
    deleted,
    method,
    suffix,
    kwargs,
):
    task_id = test_task["id"]
    url = f"/api/v1/tasks/{task_id}"
    if deleted:
        assert test_client.delete(url, headers=auth_headers_first_user).status_code == 204
    response = test_client.request(method, url + suffix, headers=auth_headers_second_user, **kwargs)
    assert response.status_code == 404
    assert response.json() == {"detail": f"Task {task_id} not found"}
    test_session.expire_all()
    stored = test_session.get(Tasks, task_id)
    assert stored.is_deleted is deleted
    assert TaskResponse.model_validate(stored).model_dump(mode="json") == test_task
    assert test_client.get("/api/v1/tasks", headers=auth_headers_second_user).json() == []
    assert test_client.get("/api/v1/tasks/stats", headers=auth_headers_second_user).json() == {
        "completed_count": 0,
        "total_tasks": 0,
    }


@pytest.mark.parametrize(
    ("method", "suffix", "kwargs"),
    [
        ("delete", "", {}),
        ("post", "/restore", {}),
        ("get", "", {}),
        ("patch", "", {"json": {}}),
        ("patch", "", {"json": {"name": "Missing"}}),
    ],
)
def test_missing_task_should_return_404(
    test_client, auth_headers_first_user, method, suffix, kwargs
):
    response = test_client.request(
        method, f"/api/v1/tasks/999999{suffix}", headers=auth_headers_first_user, **kwargs
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Task 999999 not found"}


def test_restore_active_task_should_return_409_without_changes(
    test_client, auth_headers_first_user, test_task
):
    url = f"/api/v1/tasks/{test_task['id']}"
    response = test_client.post(f"{url}/restore", headers=auth_headers_first_user)
    assert response.status_code == 409
    assert response.json() == {"detail": f"Task {test_task['id']} is already active"}
    assert test_client.get(url, headers=auth_headers_first_user).json() == test_task


@pytest.mark.parametrize("deleted", [False, True])
@pytest.mark.parametrize("method", ["delete", "post"])
@pytest.mark.parametrize("headers", [{}, {"Authorization": "Bearer invalid-token"}])
def test_unauthorized_delete_or_restore_should_return_401_without_changes(
    test_client, test_session, auth_headers_first_user, test_task, deleted, method, headers
):
    task_id = test_task["id"]
    url = f"/api/v1/tasks/{task_id}"
    if deleted:
        assert test_client.delete(url, headers=auth_headers_first_user).status_code == 204
    response = test_client.request(
        method, url + ("/restore" if method == "post" else ""), headers=headers
    )
    assert response.status_code == 401
    test_session.expire_all()
    stored = test_session.get(Tasks, task_id)
    assert stored.is_deleted is deleted
    assert TaskResponse.model_validate(stored).model_dump(mode="json") == test_task


@pytest.mark.parametrize("status_filter", [None, "active", "pending", "in_progress", "done"])
def test_list_and_stats_should_exclude_deleted_tasks_before_filtering_and_pagination(
    test_client, test_session, auth_headers_first_user, auth_headers_second_user, status_filter
):
    active_tasks = []
    for index, (status, deleted) in enumerate(
        [
            ("done", True),
            ("pending", False),
            ("pending", True),
            ("done", False),
            ("in_progress", False),
            ("in_progress", True),
            ("done", False),
            ("pending", False),
        ]
    ):
        response = test_client.post(
            "/api/v1/tasks",
            headers=auth_headers_first_user,
            json={"name": f"Task {index}", "status": status},
        )
        assert response.status_code == 201
        task = response.json()
        # Distinct creation times make the requested descending order deterministic.
        test_session.get(Tasks, task["id"]).created_at = datetime(2026, 1, index + 1)
        test_session.flush()
        if deleted:
            assert (
                test_client.delete(
                    f"/api/v1/tasks/{task['id']}", headers=auth_headers_first_user
                ).status_code
                == 204
            )
        else:
            active_tasks.insert(0, task)
    foreign = test_client.post(
        "/api/v1/tasks",
        headers=auth_headers_second_user,
        json={"name": "Other owner's completed task", "status": "done"},
    )
    assert foreign.status_code == 201

    expected = [
        task["id"]
        for task in active_tasks
        if status_filter is None
        or (status_filter == "active" and task["status"] != "done")
        or task["status"] == status_filter
    ]
    params = {"sort_by_creation_date": True}
    if status_filter:
        params["status"] = status_filter
    response = test_client.get("/api/v1/tasks", headers=auth_headers_first_user, params=params)
    assert response.status_code == 200
    assert [task["id"] for task in response.json()] == expected
    for offset in [0, 1, len(expected)]:
        page = test_client.get(
            "/api/v1/tasks",
            headers=auth_headers_first_user,
            params={**params, "limit": 2, "offset": offset},
        )
        assert page.status_code == 200
        assert [task["id"] for task in page.json()] == expected[offset : offset + 2]
    stats = test_client.get("/api/v1/tasks/stats", headers=auth_headers_first_user)
    assert stats.status_code == 200
    assert stats.json() == {"completed_count": 2, "total_tasks": 5}
