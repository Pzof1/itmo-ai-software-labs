def test_register_should_return_201_and_user_login(test_client, first_user_data):

    response = test_client.post("/api/v1/register", json=first_user_data)

    assert response.status_code == 201
    assert response.json()["login"] == "test_user"


def test_register_should_return_400_when_user_with_same_login_exist(test_client, first_user_data):

    test_client.post("/api/v1/register", json=first_user_data)
    response = test_client.post("/api/v1/register", json=first_user_data)
    assert response.status_code == 400


def test_login_should_return_200_and_token_type(test_client, first_user_data):

    test_client.post("/api/v1/register", json=first_user_data)

    response = test_client.post(
        "/api/v1/login",
        data={
            "username": first_user_data.get("login"),
            "password": first_user_data.get("password"),
        },
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"


def test_login_should_return_401_when_password_is_wrong(test_client, first_user_data):
    test_client.post("/api/v1/register", json=first_user_data)

    response = test_client.post(
        "/api/v1/login", data={"username": first_user_data.get("login"), "password": "12341234"}
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect login or password"}


def test_login_should_return_401_when_login_is_wrong(test_client, first_user_data):
    test_client.post("/api/v1/register", json=first_user_data)

    response = test_client.post(
        "/api/v1/login",
        data={"username": "some_login", "password": first_user_data.get("password")},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect login or password"}


def test_login_via_telegram_should_return_200_and_access_token(
    test_client, bot_auth_headers, tg_user_data
):
    response = test_client.post(
        "/api/v1/login/telegram", json=tg_user_data, headers=bot_auth_headers
    )

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_login_via_telegram_should_return_200_and_access_token_when_user_exist(
    test_client, bot_auth_headers, tg_user_data, registration_via_telegram, get_user_count
):
    count_before = get_user_count()
    response = test_client.post(
        "/api/v1/login/telegram", json=tg_user_data, headers=bot_auth_headers
    )

    assert get_user_count() == count_before
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_login_via_telegram_should_return_403_forbidden_without_secret_key_from_bot(
    test_client, tg_user_data
):
    response = test_client.post("/api/v1/login/telegram", json=tg_user_data)

    assert response.status_code == 403
    assert response.json()["detail"] == "Forbidden"


def test_login_via_telegram_should_return_403_forbbiden_with_invalid_secret_key_from_bot(
    test_client, tg_user_data
):
    response = test_client.post(
        "/api/v1/login/telegram", json=tg_user_data, headers={"X-Internal-Secret": "secret_key"}
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Forbidden"
