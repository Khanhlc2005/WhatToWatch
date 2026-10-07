from app.llm_client import OllamaClient


def test_ollama_structured_request_sends_schema(monkeypatch) -> None:
    calls = []

    class FakeResponse:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict[str, str]:
            return {"response": '{"status":"no_match"}'}

    def fake_post(url, json, timeout):
        calls.append((url, json, timeout))
        return FakeResponse()

    monkeypatch.setenv("OLLAMA_MODEL_NAME", "qwen2.5:3b")
    monkeypatch.setattr("app.llm_client.requests.post", fake_post)
    schema = {"type": "object", "properties": {"answer": {"type": "string"}}}
    result = OllamaClient().generate("question", "grounded system", response_format=schema)
    assert result == '{"status":"no_match"}'
    assert calls[0][1]["format"] == schema
    assert calls[0][1]["options"] == {"temperature": 0}
    assert calls[0][1]["system"] == "grounded system"
    assert calls[0][1]["stream"] is False
