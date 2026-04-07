from __future__ import annotations

from openai import OpenAI, OpenAIError

from errors import ProviderAPIError


class OpenAIService:
    def __init__(self, api_key: str, timeout: float = 30.0):
        self.api_key = api_key
        self.timeout = timeout
        self.client = OpenAI(api_key=api_key, timeout=timeout) if api_key else None

    def generate_structured_text(self, *, model: str, system_prompt: str, user_prompt: str) -> str:
        if self.client is None:
            raise ProviderAPIError(
                code="openai_not_configured",
                message="OpenAI nao esta configurado. Defina OPENAI_API_KEY no arquivo .env.",
                status_code=503,
            )

        try:
            response = self.client.chat.completions.create(
                model=model,
                temperature=0.2,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
        except OpenAIError as error:
            raise ProviderAPIError(
                code="openai_request_failed",
                message="O provedor OpenAI nao conseguiu processar a solicitacao no momento.",
                status_code=502,
            ) from error

        try:
            content = response.choices[0].message.content
        except (AttributeError, IndexError, TypeError) as error:
            raise ProviderAPIError(
                code="openai_empty_response",
                message="O provedor OpenAI retornou uma resposta vazia.",
                status_code=502,
            ) from error

        if not content:
            raise ProviderAPIError(
                code="openai_empty_response",
                message="O provedor OpenAI retornou uma resposta vazia.",
                status_code=502,
            )

        return content
