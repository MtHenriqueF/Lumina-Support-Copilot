from __future__ import annotations

from app import create_app


class FakeOpenAIService:
    def __init__(self, response_text: str):
        self.response_text = response_text

    def generate_structured_text(self, *, model: str, system_prompt: str, user_prompt: str) -> str:
        return self.response_text


def build_client(response_text: str = ""):
    app = create_app(
        test_config={
            "TESTING": True,
            "OPENAI_API_KEY": "test-key",
        },
        openai_service=FakeOpenAIService(response_text),
    )
    return app.test_client()


def test_generate_success():
    client = build_client(
        """
        {
          "summary": "Cliente relata falha no login apos redefinir a senha.",
          "sentiment": 28,
          "category": "technical",
          "priority": "High",
          "language": "pt-BR",
          "is_resolved": false,
          "tags": ["login", "senha"],
          "action": "Validar o fluxo de autenticacao e revisar logs do erro 500.",
          "response": "Entendi o problema e ja organizei os proximos passos para a analise tecnica."
        }
        """.strip()
    )

    response = client.post(
        "/generate",
        json={
            "message": "Nao consigo entrar na conta depois de redefinir a senha.",
            "model": "fast",
        },
    )

    payload = response.get_json()
    assert response.status_code == 200
    assert payload["category"] == "technical"
    assert payload["priority"] == "High"
    assert payload["model"] == "fast"
    assert "duration" in payload


def test_generate_rejects_invalid_model():
    client = build_client()

    response = client.post(
        "/generate",
        json={
            "message": "Preciso de ajuda com uma cobranca.",
            "model": "legacy",
        },
    )

    payload = response.get_json()
    assert response.status_code == 400
    assert payload["error"]["code"] == "invalid_model"


def test_generate_rejects_missing_json():
    client = build_client()

    response = client.post("/generate")

    payload = response.get_json()
    assert response.status_code == 400
    assert payload["error"]["code"] == "json_required"


def test_generate_rejects_empty_message():
    client = build_client()

    response = client.post(
        "/generate",
        json={
            "message": "   ",
            "model": "balanced",
        },
    )

    payload = response.get_json()
    assert response.status_code == 400
    assert payload["error"]["code"] == "message_required"


def test_generate_uses_fallback_when_model_returns_invalid_json():
    client = build_client("Resposta livre sem nenhum JSON valido.")

    response = client.post(
        "/generate",
        json={
            "message": "O cliente relata erro 500 e nao consegue acessar o painel.",
            "model": "smart",
        },
    )

    payload = response.get_json()
    assert response.status_code == 200
    assert payload["model"] == "smart"
    assert payload["category"] == "technical"
    assert payload["priority"] in {"Medium", "High", "Critical"}
    assert isinstance(payload["tags"], list)
    assert payload["response"]
