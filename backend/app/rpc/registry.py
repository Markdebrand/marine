from typing import Any, Callable, Dict
import inspect

class RpcRegistry:
    def __init__(self):
        self._handlers: dict[str, Callable[..., Any]] = {}

    def register(self, name: str, func: Callable[..., Any]):
        key = name.lower()
        self._handlers[key] = func

    def get(self, name: str) -> Callable[..., Any] | None:
        return self._handlers.get(name.lower())

    async def call(self, name: str, params: Dict[str, Any] | None = None):
        params = params or {}
        func = self.get(name)
        if not func:
            raise ValueError("RPC method not found")
        if inspect.iscoroutinefunction(func):
            return await func(**params)
        return func(**params)

# Instancia global simple (opcionalmente inyectable)
rpc_registry = RpcRegistry()
