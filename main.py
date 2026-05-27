from fastapi import FastAPI, Request
from app.api.lifespan import lifespan
from app.api.routers import query_router
from app.core.context import request_id_context_var
import uuid

# 创建FastAPI应用，并注册生命周期函数
app = FastAPI(lifespan=lifespan) 
# 注册路由
app.include_router(query_router)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    # 请求处理前
    request_id = uuid.uuid4()
    request_id_context_var.set(request_id)
    response = await call_next(request) 

    # 请求处理后
    return response




if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
        
