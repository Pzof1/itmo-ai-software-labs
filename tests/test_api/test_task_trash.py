import pytest

from app.models import Tasks


def test_trash_should_show_only_owners_deleted_tasks_in_id_order_without_writing(
    test_client, test_session, auth_headers_first_user, auth_headers_second_user
):
    own = []
    for index in range(4):
        response = test_client.post(
            "/api/v1/tasks", headers=auth_headers_first_user, json={"name": f"Own {index}"}
        )
        assert response.status_code == 201
        own.append(response.json())
    foreign = test_client.post(
        "/api/v1/tasks", headers=auth_headers_second_user, json={"name": "Foreign"}
    ).json()
    for task in (own[0], own[2], foreign):
        assert (
            test_client.delete(
                f"/api/v1/tasks/{task['id']}",
                headers=auth_headers_second_user if task == foreign else auth_headers_first_user,
            ).status_code
            == 204
        )

    response = test_client.get("/api/v1/tasks/trash", headers=auth_headers_first_user)
    assert response.status_code == 200
    assert response.json() == [own[0], own[2]]
    assert "owner_id" not in response.json()[0]
    assert "is_deleted" not in response.json()[0]
    test_session.expire_all()
    assert [test_session.get(Tasks, task["id"]).is_deleted for task in own] == [
        True, False, True, False
    ]
    assert test_session.get(Tasks, foreign["id"]).is_deleted is True
    assert test_client.get("/api/v1/tasks/trash", headers=auth_headers_second_user).json() == [
        foreign
    ]
    assert {task["id"] for task in test_client.get(
        "/api/v1/tasks", headers=auth_headers_first_user
    ).json()} == {own[1]["id"], own[3]["id"]}
    assert test_client.get("/api/v1/tasks/stats", headers=auth_headers_first_user).json() == {
        "completed_count": 0,
        "total_tasks": 2,
    }


def test_trash_should_paginate_after_filtering_with_defaults_and_boundaries(
    test_client, auth_headers_first_user, auth_headers_second_user
):
    deleted = []
    for index in range(13):
        owner = auth_headers_second_user if index == 3 else auth_headers_first_user
        task = test_client.post(
            "/api/v1/tasks", headers=owner, json={"name": f"Task {index}"}
        ).json()
        if index != 5:
            assert test_client.delete(f"/api/v1/tasks/{task['id']}", headers=owner).status_code == 204
            if index != 3:
                deleted.append(task)

    url = "/api/v1/tasks/trash"
    assert test_client.get(url, headers=auth_headers_first_user).json() == deleted[:10]
    assert test_client.get(
        url, headers=auth_headers_first_user, params={"limit": 1, "offset": 1}
    ).json() == deleted[1:2]
    assert test_client.get(
        url, headers=auth_headers_first_user, params={"limit": 100, "offset": 10}
    ).json() == deleted[10:]
    assert test_client.get(
        url, headers=auth_headers_first_user, params={"offset": len(deleted)}
    ).json() == []
    assert test_client.get(
        url, headers=auth_headers_first_user, params={"offset": 999}
    ).json() == []


@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 101}, {"offset": -1}])
def test_invalid_trash_pagination_should_return_422(test_client, auth_headers_first_user, params):
    response = test_client.get("/api/v1/tasks/trash", headers=auth_headers_first_user, params=params)
    assert response.status_code == 422


def test_trash_should_be_empty_and_follow_restore_and_redelete(
    test_client, auth_headers_first_user, test_task
):
    url = "/api/v1/tasks/trash"
    task_url = f"/api/v1/tasks/{test_task['id']}"
    assert test_client.get(url, headers=auth_headers_first_user).json() == []
    assert test_client.delete(task_url, headers=auth_headers_first_user).status_code == 204
    assert test_client.get(url, headers=auth_headers_first_user).json() == [test_task]
    assert test_client.post(f"{task_url}/restore", headers=auth_headers_first_user).status_code == 200
    assert test_client.get(url, headers=auth_headers_first_user).json() == []
    assert test_client.delete(task_url, headers=auth_headers_first_user).status_code == 204
    assert test_client.get(url, headers=auth_headers_first_user).json() == [test_task]


@pytest.mark.parametrize("headers", [{}, {"Authorization": "Bearer invalid-token"}])
def test_unauthorized_trash_should_return_401(test_client, headers):
    assert test_client.get("/api/v1/tasks/trash", headers=headers).status_code == 401
