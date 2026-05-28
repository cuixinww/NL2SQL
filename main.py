from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.api.lifespan import lifespan
from app.api.routers import query_router, health_router
from app.core.context import request_id_context_var
import uuid
import time

app = FastAPI(lifespan=lifespan, title="银行问数 NL2SQL", version="0.1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(health_router)
app.include_router(query_router)


@app.middleware("http")
async def add_request_context(request: Request, call_next):
    request_id = uuid.uuid4()
    request_id_context_var.set(request_id)
    start = time.monotonic()
    response = await call_next(request)
    elapsed = time.monotonic() - start
    response.headers["X-Request-ID"] = str(request_id)
    response.headers["X-Process-Time"] = f"{elapsed:.3f}"
    return response


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
