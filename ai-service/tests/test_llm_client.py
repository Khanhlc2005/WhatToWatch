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
    assert calls[0][1]["options"] == {"temperature": 0, "num_predict": 512}
    assert calls[0][2] == (5, 300)
    assert calls[0][1]["system"] == "grounded system"
    assert calls[0][1]["stream"] is False


def test_ollama_uses_selected_model_tag(monkeypatch) -> None:
    class FakeResponse:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict[str, str]:
            return {"response": "ok"}

    calls = []

    def fake_post(url, json, timeout):
        calls.append(json)
        return FakeResponse()

    monkeypatch.setenv("OLLAMA_MODEL_NAME", "whattowatch-qwen25-3b-sft:english-v1")
    monkeypatch.setattr("app.llm_client.requests.post", fake_post)
    assert OllamaClient().generate("question") == "ok"
    assert calls[0]["model"] == "whattowatch-qwen25-3b-sft:english-v1"
