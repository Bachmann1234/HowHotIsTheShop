from howhot.app import app


def test_app() -> None:
    with app.test_client() as client:
        response = client.get("/")
        assert b"Hello, World!" in response.data
