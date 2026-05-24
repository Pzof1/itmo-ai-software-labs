def test_create_task_should_return_201_and_task_data(
    test_client, auth_headers_first_user, base_task_data
):
    response = test_client.post(
        "/api/v1/tasks", headers=auth_headers_first_user, json=base_task_data
    )
    assert response.status_code == 201
    assert response.json().get("id") is not None
    assert response.json().get("name") == "Buy flowers"
    assert response.json().get("description") == "Don't forget water the flowers"
    assert response.json().get("priority") == "high"


def test_create_task_should_return_401_when_unauthorized(test_client):
    response = test_client.post("/api/v1/tasks", json={"name": "unauthorized task"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_get_all_tasks_should_return_tasks_for_owner(
    test_client, auth_headers_first_user, test_task
):

    response = test_client.get("/api/v1/tasks", headers=auth_headers_first_user)

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert response.json()[0]["name"] == "do smth"


def test_get_all_tasks_should_return_empty_list_for_other_user(
    test_client, auth_headers_second_user, test_task
):
    response = test_client.get("/api/v1/tasks", headers=auth_headers_second_user)

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert not bool(response.json())


def test_get_all_tasks_should_return_401_when_unauthorized(test_client):
    response = test_client.get("/api/v1/tasks")

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_get_task_by_id_should_return_task_for_owner(
    test_client, auth_headers_first_user, test_task
):
    task_id = test_task["id"]

    response = test_client.get(f"/api/v1/tasks/{task_id}", headers=auth_headers_first_user)

    assert response.status_code == 200
    assert response.json()["name"] == "do smth"
    assert response.json()["description"] == "tomorrow"


def test_get_task_by_id_should_return_404_for_non_owner(
    test_client, auth_headers_second_user, test_task
):
    task_id_created_by_first_user = test_task["id"]

    response = test_client.get(
        f"/api/v1/tasks/{task_id_created_by_first_user}", headers=auth_headers_second_user
    )

    assert response.status_code == 404
    assert response.json() == {"detail": f"Task {task_id_created_by_first_user} not found"}


def test_get_task_by_id_should_return_401_when_unauthorized(test_client):
    response = test_client.get("/api/v1/tasks/1")

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_update_task_should_return_updated_data(
    test_client, auth_headers_first_user, test_task, base_patch_data
):
    task_id = test_task["id"]

    response = test_client.patch(
        f"/api/v1/tasks/{task_id}", headers=auth_headers_first_user, json=base_patch_data
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Updated task name"
    assert response.json()["priority"] == "medium"
    assert response.json()["description"] == "tomorrow"  # unchanged field


def test_update_task_should_return_404_for_non_owner(
    test_client, auth_headers_second_user, test_task, base_patch_data
):
    task_id_created_by_first_user = test_task["id"]

    response = test_client.patch(
        f"/api/v1/tasks/{task_id_created_by_first_user}",
        headers=auth_headers_second_user,
        json=base_patch_data,
    )

    assert response.status_code == 404
    assert response.json() == {"detail": f"Task {task_id_created_by_first_user} not found"}


def test_update_task_should_return_401_when_unauthorized(test_client, base_patch_data):
    response = test_client.patch("/api/v1/tasks/1", json=base_patch_data)

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_update_task_should_return_task_without_changes_when_update_data_empty(
    test_client, auth_headers_first_user, test_task
):
    task_id = test_task["id"]
    response = test_client.patch(
        f"/api/v1/tasks/{task_id}", headers=auth_headers_first_user, json={}
    )

    assert response.json()["id"] == task_id
    assert response.json()["name"] == "do smth"
    assert response.json()["description"] == "tomorrow"


def test_delete_task_should_return_204_for_owner(test_client, auth_headers_first_user, test_task):
    task_id = test_task["id"]

    response = test_client.delete(f"/api/v1/tasks/{task_id}", headers=auth_headers_first_user)

    assert response.status_code == 204


def test_delete_task_should_return_404_for_non_owner(
    test_client, test_task, auth_headers_second_user
):
    task_id_created_by_first_user = test_task["id"]

    response = test_client.delete(
        f"/api/v1/tasks/{task_id_created_by_first_user}", headers=auth_headers_second_user
    )

    assert response.status_code == 404
    assert response.json() == {"detail": f"Task {task_id_created_by_first_user} not found"}


def test_delete_task_should_return_401_when_unauthorized(test_client):
    response = test_client.delete("/api/v1/tasks/1")

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_get_stats_should_return_correct_pydantic_model_and_200(
    test_client, auth_headers_first_user, test_task
):
    response = test_client.get("/api/v1/tasks/stats", headers=auth_headers_first_user)

    assert response.status_code == 200
    assert response.json() == {"completed_count": 0, "total_tasks": 1}


def test_get_stats_should_return_401_when_unathorized(test_client):
    response = test_client.get("/api/v1/tasks/stats")

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}
