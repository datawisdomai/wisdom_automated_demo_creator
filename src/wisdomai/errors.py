from __future__ import annotations


class WisdomAIError(Exception):
    pass


class GraphQLError(WisdomAIError):
    def __init__(self, errors: list[dict], operation: str | None = None):
        self.errors = errors
        self.operation = operation
        msg = "; ".join(e.get("message", str(e)) for e in errors)
        suffix = f" in {operation}" if operation else ""
        super().__init__(f"GraphQL error{suffix}: {msg}")


class MutationStatusError(WisdomAIError):
    def __init__(self, code: str, message: str, operation: str | None = None):
        self.code = code
        self.message = message
        self.operation = operation
        super().__init__(f"{operation or 'mutation'} returned {code}: {message}")
