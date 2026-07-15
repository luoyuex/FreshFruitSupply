from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import admin, auth, public
from app.core.config import settings
from app.services.order_maintenance import start_unpaid_order_closer


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动待支付订单超时关单后台任务，应用关闭时取消
    closer_task = start_unpaid_order_closer()
    try:
        yield
    finally:
        closer_task.cancel()


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

settings.upload_root.mkdir(parents=True, exist_ok=True)
app.mount('/uploads', StaticFiles(directory=str(settings.upload_root)), name='uploads')

app.include_router(public.router, prefix=settings.api_prefix)
app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(admin.router, prefix=settings.api_prefix)


@app.get('/health')
def health():
    return {'status': 'ok'}
