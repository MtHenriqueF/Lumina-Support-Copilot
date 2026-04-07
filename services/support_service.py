from __future__ import annotations

import json
import logging
import re
import time

from pydantic import ValidationError as PydanticValidationError

from errors import InternalAPIError, ProviderAPIError
from schemas.support import SupportTicketResponse
from utils.logging import log_event

logger = logging.getLogger("lumina.services.support")

SYSTEM_PROMPT = """
You are Lumina Support Copilot, a technical support and customer care copilot.
Your job is to classify customer tickets, summarize the issue, detect language,
estimate priority, recommend the next action, and draft a clear reply for the customer.

Behavior rules:
- Be clear, empathetic, professional, and action-oriented.
- Do not invent policies, SLAs, refunds, deadlines, or facts not confirmed by the user.
- Respect the user's language in the "response" and "action" fields.
- If the issue cannot be fully solved from the message alone, set "is_resolved" to false.
- Keep tags short and practical for search and routing.
- Set "sentiment" to an integer from 0 to 100 based on the user's tone:
  0-20 very negative, 21-40 negative, 41-60 neutral, 61-80 positive, 81-100 very positive.
- Do not use 0 as a placeholder. Choose the best estimated score from the message.
- Return only a JSON object with the exact schema below.

Schema:
{
  "summary": "string",
  "sentiment": "integer from 0 to 100",
  "category": "technical|billing|general",
  "priority": "Low|Medium|High|Critical",
  "language": "language code like pt-BR or en",
  "is_resolved": false,
  "tags": ["string"],
  "action": "string",
  "response": "string"
}
""".strip()

PORTUGUESE_HINTS = {
    "ajuda",
    "boleto",
    "cobranca",
    "cobrança",
    "erro",
    "falha",
    "fatura",
    "login",
    "nao",
    "não",
    "pagamento",
    "preciso",
    "problema",
    "senha",
    "suporte",
}
SPANISH_HINTS = {
    "ayuda",
    "factura",
    "inicio",
    "necesito",
    "pedido",
    "problema",
    "reembolso",
    "soporte",
    "tarjeta",
}
BILLING_KEYWORDS = {
    "assinatura",
    "billing",
    "charge",
    "charged",
    "checkout",
    "cobranca",
    "cobrança",
    "fatura",
    "invoice",
    "pagamento",
    "payment",
    "plano",
    "refund",
    "reembolso",
    "subscription",
}
TECHNICAL_KEYWORDS = {
    "500",
    "api",
    "bug",
    "crash",
    "erro",
    "error",
    "falha",
    "failure",
    "integracao",
    "integração",
    "login",
    "password",
    "senha",
    "timeout",
    "travou",
}
HIGH_PRIORITY_KEYWORDS = {
    "asap",
    "blocked",
    "bloqueado",
    "canot",
    "can't",
    "cannot",
    "critical",
    "down",
    "falha",
    "fora",
    "frustrado",
    "imediato",
    "indisponivel",
    "indisponível",
    "outage",
    "security",
    "seguranca",
    "segurança",
    "urgent",
    "urgente",
}
LOW_SENTIMENT_KEYWORDS = {
    "angry",
    "awful",
    "frustrado",
    "furious",
    "hate",
    "horrivel",
    "horrível",
    "inadmissivel",
    "inadmissível",
    "irritado",
    "péssimo",
    "ridiculous",
    "terrible",
    "unacceptable",
}
STOPWORDS = {
    "about",
    "after",
    "agora",
    "ainda",
    "ajuda",
    "already",
    "antes",
    "because",
    "cliente",
    "como",
    "com",
    "does",
    "estou",
    "issue",
    "mais",
    "message",
    "nao",
    "não",
    "para",
    "pelo",
    "please",
    "preciso",
    "problem",
    "quando",
    "quero",
    "sobre",
    "suporte",
    "that",
    "this",
    "ticket",
    "with",
}


class SupportCopilotService:
    def __init__(self, openai_service):
        self.openai_service = openai_service

    def generate_ticket_payload(self, *, user_message: str, model_alias: str, model_id: str) -> dict:
        started_at = time.perf_counter()

        try:
            raw_response = self.openai_service.generate_structured_text(
                model=model_id,
                system_prompt=SYSTEM_PROMPT,
                user_prompt=user_message,
            )
            payload, parse_success = self._parse_response(raw_response, user_message)
        except ProviderAPIError:
            inference_duration = round((time.perf_counter() - started_at) * 1000, 2)
            log_event(
                logger,
                "error",
                "provider_error",
                model_alias=model_alias,
                provider_model=model_id,
                input_chars=len(user_message),
                inference_duration_ms=inference_duration,
                error_type="ProviderAPIError",
            )
            raise
        except Exception as error:
            inference_duration = round((time.perf_counter() - started_at) * 1000, 2)
            log_event(
                logger,
                "error",
                "unexpected_service_error",
                model_alias=model_alias,
                provider_model=model_id,
                input_chars=len(user_message),
                inference_duration_ms=inference_duration,
                error_type=type(error).__name__,
            )
            raise InternalAPIError() from error

        inference_duration = round((time.perf_counter() - started_at) * 1000, 2)
        log_event(
            logger,
            "info",
            "ticket_generated",
            model_alias=model_alias,
            provider_model=model_id,
            input_chars=len(user_message),
            inference_duration_ms=inference_duration,
            parse_success=parse_success,
        )
        return payload.model_dump()

    def _parse_response(self, raw_response: str, user_message: str) -> tuple[SupportTicketResponse, bool]:
        candidate_json = self._extract_json_object(raw_response)
        if candidate_json:
            try:
                parsed_payload = json.loads(candidate_json)
                payload = SupportTicketResponse.model_validate(parsed_payload)
                payload = self._repair_payload(payload, user_message)
                return payload, True
            except (json.JSONDecodeError, PydanticValidationError) as error:
                log_event(
                    logger,
                    "warning",
                    "parse_failed",
                    error_type=type(error).__name__,
                    extracted_json=True,
                )

        fallback_payload = self._build_fallback_payload(user_message)
        return fallback_payload, False

    def _repair_payload(self, payload: SupportTicketResponse, user_message: str) -> SupportTicketResponse:
        heuristic_sentiment = self._infer_sentiment(user_message)
        repaired_payload = payload.model_copy(
            update={
                "tags": payload.tags or self._extract_tags(user_message),
                "summary": payload.summary or self._build_summary(user_message),
            }
        )

        # Some model responses mirror the schema example and keep sentiment at 0.
        if payload.sentiment == 0 and heuristic_sentiment > 0:
            repaired_payload = repaired_payload.model_copy(update={"sentiment": heuristic_sentiment})

        return repaired_payload

    def _extract_json_object(self, raw_response: str) -> str | None:
        fenced_match = re.search(r"```json\s*(\{.*?\})\s*```", raw_response, flags=re.DOTALL | re.IGNORECASE)
        if fenced_match:
            return fenced_match.group(1)

        start_index = raw_response.find("{")
        if start_index == -1:
            return None

        depth = 0
        in_string = False
        escape_next = False

        for index in range(start_index, len(raw_response)):
            character = raw_response[index]

            if escape_next:
                escape_next = False
                continue

            if character == "\\":
                escape_next = True
                continue

            if character == '"':
                in_string = not in_string
                continue

            if in_string:
                continue

            if character == "{":
                depth += 1
            elif character == "}":
                depth -= 1
                if depth == 0:
                    return raw_response[start_index : index + 1]

        return None

    def _build_fallback_payload(self, user_message: str) -> SupportTicketResponse:
        language = self._detect_language(user_message)
        category = self._infer_category(user_message)
        priority = self._infer_priority(user_message)
        sentiment = self._infer_sentiment(user_message)
        tags = self._extract_tags(user_message)
        action = self._build_action(language, category, priority)
        response = self._build_response(language, category)

        return SupportTicketResponse.model_validate(
            {
                "summary": self._build_summary(user_message),
                "sentiment": sentiment,
                "category": category,
                "priority": priority,
                "language": language,
                "is_resolved": False,
                "tags": tags,
                "action": action,
                "response": response,
            }
        )

    def _detect_language(self, user_message: str) -> str:
        text = user_message.lower()
        if any(token in text for token in PORTUGUESE_HINTS):
            return "pt-BR"
        if any(token in text for token in SPANISH_HINTS):
            return "es"
        return "en"

    def _infer_category(self, user_message: str) -> str:
        text = user_message.lower()
        if any(token in text for token in BILLING_KEYWORDS):
            return "billing"
        if any(token in text for token in TECHNICAL_KEYWORDS):
            return "technical"
        return "general"

    def _infer_priority(self, user_message: str) -> str:
        text = user_message.lower()
        if "critical" in text or "security" in text:
            return "Critical"
        if any(token in text for token in HIGH_PRIORITY_KEYWORDS):
            return "High"
        if len(text) > 280:
            return "Medium"
        return "Medium"

    def _infer_sentiment(self, user_message: str) -> int:
        text = user_message.lower()
        if any(token in text for token in LOW_SENTIMENT_KEYWORDS):
            return 25
        if "thanks" in text or "obrigado" in text or "obrigada" in text:
            return 70
        return 48

    def _build_summary(self, user_message: str) -> str:
        compact_text = re.sub(r"\s+", " ", user_message).strip()
        if not compact_text:
            return "Solicitacao de suporte recebida para revisao."

        if len(compact_text) <= 180:
            return compact_text

        return f"{compact_text[:177].rstrip()}..."

    def _extract_tags(self, user_message: str) -> list[str]:
        tokens = re.findall(r"[a-zA-ZÀ-ÿ0-9_-]{4,}", user_message.lower())
        tags: list[str] = []
        for token in tokens:
            if token in STOPWORDS or token in tags:
                continue
            tags.append(token)
            if len(tags) == 6:
                break

        return tags or ["support"]

    def _build_action(self, language: str, category: str, priority: str) -> str:
        if language.startswith("pt"):
            if category == "technical":
                base_action = "Validar ambiente, passos para reproducao e mensagens de erro antes de escalar."
            elif category == "billing":
                base_action = "Conferir cobrancas, status da assinatura e historico da transacao antes de responder."
            else:
                base_action = "Confirmar contexto adicional e direcionar o caso para a fila correta."

            if priority in {"High", "Critical"}:
                return f"{base_action} Tratar com prioridade elevada e atualizar o cliente rapidamente."
            return base_action

        if language == "es":
            if category == "technical":
                return "Validar entorno, pasos para reproducir y mensajes de error antes de escalar."
            if category == "billing":
                return "Revisar cobros, estado de la suscripcion y datos de la transaccion antes de responder."
            return "Confirmar contexto adicional y dirigir el caso al flujo correcto."

        if category == "technical":
            return "Validate the environment, reproduction steps, and error details before escalating."
        if category == "billing":
            return "Review charges, subscription state, and transaction history before replying."
        return "Confirm the missing context and route the case to the right support workflow."

    def _build_response(self, language: str, category: str) -> str:
        if language.startswith("pt"):
            if category == "billing":
                return (
                    "Entendi sua solicitacao. Vou deixar a analise organizada para revisar a cobranca "
                    "ou a assinatura e seguir com a proxima acao recomendada."
                )
            if category == "technical":
                return (
                    "Entendi o problema. Ja organizei os pontos principais para acelerar a analise "
                    "tecnica e orientar o proximo passo com clareza."
                )
            return (
                "Recebi sua solicitacao e consolidei as informacoes principais para encaminhar o atendimento "
                "de forma objetiva."
            )

        if language == "es":
            return (
                "Recibi tu solicitud y organicé los puntos principales para avanzar con una respuesta "
                "clara y el siguiente paso recomendado."
            )

        if category == "technical":
            return (
                "I captured the key issue details and organized the next technical step so support can move "
                "forward clearly."
            )
        if category == "billing":
            return (
                "I captured the billing context and prepared the next review step so the team can respond "
                "with clarity."
            )
        return (
            "I captured the main context and organized the next recommended step so the support team can respond "
            "clearly."
        )
