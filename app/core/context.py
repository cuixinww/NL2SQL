from contextvars import ContextVar

# 请求id上下文变量
request_id_context_var:ContextVar[str] = ContextVar("request_id", default="init")
