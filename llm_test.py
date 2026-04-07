from __future__ import annotations

import json

from model import generate_response


def call_all_models(user_prompt: str) -> None:
    for alias in ("fast", "balanced", "smart"):
        result = generate_response(alias, user_prompt)
        print(f"{alias.upper()} Response:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print()


if __name__ == "__main__":
    call_all_models(
        "O cliente nao consegue redefinir a senha e informa que o erro acontece em todos os navegadores."
    )
