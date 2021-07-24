from howhot.app import app, get_redis


def test_app() -> None:
    with app.test_client() as client:
        response = client.get("/")
        assert response.status_code == 200
