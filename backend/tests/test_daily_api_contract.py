from app.api.v1.daily import create_daily_session


def test_daily_api_is_registered() -> None:
    assert create_daily_session.__name__ == "create_daily_session"
