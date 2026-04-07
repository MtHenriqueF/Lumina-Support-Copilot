from __future__ import annotations

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from openai import APIConnectionError, APIStatusError, AuthenticationError, PermissionDeniedError, RateLimitError

from errors import ProviderAPIError


class LangChainSupportService:
    def __init__(self, api_key: str, timeout: float = 30.0, model_aliases: dict[str, str] | None = None):
        self.api_key = api_key
        self.timeout = timeout
        self.model_aliases = model_aliases or {}
        self.ready = bool(api_key)

        if not api_key:
            return

        if not self.model_aliases:
            raise ProviderAPIError(
                code="provider_not_configured",
                message="Nenhum modelo foi configurado para a cadeia LangChain.",
                status_code=500,
            )

        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "{system_prompt}\n\n{format_instructions}"),
                ("human", "{user_prompt}"),
            ]
        )
        self.output_parser = StrOutputParser()

    def generate_structured_text(
        self,
        *,
        model_alias: str,
        system_prompt: str,
        user_prompt: str,
        format_instructions: str,
    ) -> str:
        if not self.ready:
            raise ProviderAPIError(
                code="openai_not_configured",
                message="OpenAI nao esta configurado. Defina OPENAI_API_KEY no arquivo .env.",
                status_code=503,
            )

        if model_alias not in self.model_aliases:
            raise ProviderAPIError(
                code="openai_model_not_configured",
                message="O alias de modelo solicitado nao esta configurado.",
                status_code=500,
            )

        try:
            model = ChatOpenAI(
                api_key=self.api_key,
                model=self.model_aliases[model_alias],
                timeout=self.timeout,
                temperature=0.2,
            )
            chain = self.prompt | model | self.output_parser
            return chain.invoke(
                {
                    "system_prompt": system_prompt,
                    "user_prompt": user_prompt,
                    "format_instructions": format_instructions,
                }
            )
        except AuthenticationError as error:
            raise ProviderAPIError(
                code="openai_authentication_failed",
                message="A chave da OpenAI e invalida, expirou ou nao foi carregada corretamente do arquivo .env.",
                status_code=401,
            ) from error
        except PermissionDeniedError as error:
            raise ProviderAPIError(
                code="openai_permission_denied",
                message="A conta ou projeto atual nao tem permissao para usar o modelo configurado.",
                status_code=403,
            ) from error
        except RateLimitError as error:
            raise ProviderAPIError(
                code="openai_rate_limited",
                message="O limite de requisicoes da OpenAI foi atingido. Tente novamente em instantes.",
                status_code=429,
            ) from error
        except APIConnectionError as error:
            raise ProviderAPIError(
                code="openai_connection_failed",
                message="Nao foi possivel conectar a OpenAI. Verifique sua rede e tente novamente.",
                status_code=503,
            ) from error
        except APIStatusError as error:
            status_code = getattr(error, "status_code", 502) or 502
            if status_code == 401:
                raise ProviderAPIError(
                    code="openai_authentication_failed",
                    message="A chave da OpenAI e invalida, expirou ou nao foi carregada corretamente do arquivo .env.",
                    status_code=401,
                ) from error
            if status_code == 403:
                raise ProviderAPIError(
                    code="openai_permission_denied",
                    message="A conta ou projeto atual nao tem permissao para usar o modelo configurado.",
                    status_code=403,
                ) from error
            if status_code == 429:
                raise ProviderAPIError(
                    code="openai_rate_limited",
                    message="O limite de requisicoes da OpenAI foi atingido. Tente novamente em instantes.",
                    status_code=429,
                ) from error
            raise ProviderAPIError(
                code="openai_request_failed",
                message="O provedor OpenAI retornou um erro ao processar a solicitacao.",
                status_code=502,
            ) from error
        except Exception as error:
            raise ProviderAPIError(
                code="openai_request_failed",
                message="O provedor OpenAI nao conseguiu processar a solicitacao no momento.",
                status_code=502,
            ) from error
