from app.api.v1.memory import list_due_retrieval


def test_due_retrieval_api_is_registered() -> None:
    assert list_due_retrieval.__name__ == "list_due_retrieval"
