# Lumina Support Copilot

AI support copilot built with Flask and OpenAI for structured ticket analysis, prioritization, sentiment detection, recommended actions, and customer-ready replies.

## Overview

Lumina Support Copilot transforms raw customer messages into a structured support payload that helps agents and teams act faster. The application classifies the ticket, detects language, estimates sentiment, suggests a priority level, recommends the next operational step, and drafts a professional reply for the customer.

The project was designed as a portfolio-ready support workspace with:

- Flask backend organized with routes, services, schemas, and centralized configuration
- LangChain + LCEL orchestration over OpenAI models
- Pydantic validation for structured responses
- Resilient parsing and safe fallback behavior when the model returns invalid JSON
- Dashboard-style frontend with chat, insights panel, and responsive UX

## Demo

Demo preview for GitHub:

```text
docs/lumina-demo.gif
```

![Lumina Support Copilot Demo](./docs/lumina-demo.gif)

Full video:

[Watch the demo video](./docs/lumina-demo.mp4)

You can also add screenshots such as:

```text
docs/dashboard.png
docs/insights-panel.png
```

## Features

- Structured ticket analysis with the fields `summary`, `sentiment`, `category`, `priority`, `language`, `is_resolved`, `tags`, `action`, and `response`
- Multiple model profiles exposed as `fast`, `balanced`, and `smart`
- Request validation for missing JSON, empty messages, invalid model selection, and max input length
- Standardized JSON error responses for `400`, `404`, `405`, and `500`
- Structured logging for observability
- Safe fallback generation if the model response cannot be parsed correctly
- Modern support dashboard UI with prompt suggestions, loading states, badges, chips, and responsive layout

## Tech Stack

- Python
- Flask
- LangChain
- LangChain OpenAI
- OpenAI API
- Pydantic
- python-dotenv
- HTML, CSS, JavaScript

## Project Structure

```text
.
├── app.py
├── config.py
├── errors.py
├── requirements.txt
├── routes/
│   └── support.py
├── schemas/
│   └── support.py
├── services/
│   ├── langchain_service.py
│   └── support_service.py
├── static/
│   ├── script.js
│   └── styles.css
├── templates/
│   └── index.html
├── tests/
│   └── test_generate.py
└── utils/
    └── logging.py
```

## Local Setup

1. Clone the repository.
2. Create a virtual environment.
3. Install dependencies.
4. Create your `.env` from `.env.example`.
5. Add your `OPENAI_API_KEY`.
6. Run the Flask application.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python3 app.py
```

If port `5000` is already in use, stop the old process or run on another port.

## Environment Variables

Example configuration:

```env
APP_NAME=Lumina Support Copilot
APP_SUBTITLE=Classifique tickets, priorize atendimento e gere respostas claras com suporte de IA.
APP_ENV=development
FLASK_DEBUG=false
LOG_LEVEL=INFO
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL_FAST=gpt-4o-mini
OPENAI_MODEL_BALANCED=gpt-4.1-mini
OPENAI_MODEL_SMART=gpt-4.1
DEFAULT_MODEL_ALIAS=balanced
MESSAGE_MAX_CHARS=4000
OPENAI_TIMEOUT_SECONDS=30
```

## API Contract

`POST /generate`

Request:

```json
{
  "message": "O cliente relata falha no login e erro 500 ao redefinir a senha.",
  "model": "fast"
}
```

Response:

```json
{
  "summary": "Cliente relata falha no login e erro ao redefinir a senha.",
  "sentiment": 28,
  "category": "technical",
  "priority": "High",
  "language": "pt-BR",
  "is_resolved": false,
  "tags": ["login", "senha", "erro"],
  "action": "Validar o fluxo de autenticacao e revisar logs do erro antes de escalar.",
  "response": "Entendi o problema e organizei os proximos passos para acelerar a analise tecnica.",
  "duration": 1.42,
  "model": "fast"
}
```

## Prompt Examples

Use these examples to test the application:

```text
O cliente informa que, desde a última atualização, não consegue acessar a conta no portal web. Ao tentar fazer login, recebe erro 500 e a redefinição de senha também falha. Ele diz que a equipe está parada por causa disso e pede uma solução urgente ainda hoje. Responda em português.
```

```text
Recebi uma cobrança duplicada na minha assinatura deste mês. O valor apareceu duas vezes no cartão e preciso entender se houve renovação indevida e como será feito o estorno. Responda em português.
```

```text
The customer says the onboarding email never arrived, cannot complete setup, and wants a clear next step without waiting for a generic response. Respond in English.
```

```text
Um cliente relata lentidão extrema no painel administrativo, falhas intermitentes ao salvar dados e reclama que isso já impacta a operação da equipe comercial. Responda em português.
```

```text
The customer is asking whether their support issue is already resolved because they can log in again, but they are still unsure if the billing impact has been fixed. Respond in English.
```

## Testing

Basic route coverage is available in:

- `tests/test_generate.py`

Suggested command:

```bash
pytest
```

## Future Improvements

- Persist chat history and structured tickets in a database
- Add authentication and multi-user support
- Introduce tracing and error monitoring
- Add streaming responses for a more dynamic UX
- Support richer analytics dashboards for support operations

## Portfolio Positioning

This project is suitable for showcasing:

- backend architecture with clean separation of concerns
- robust API design and error handling
- LLM integration with structured output validation
- practical frontend UX for AI-assisted workflows
- product-oriented thinking beyond a simple chat interface
