from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine, SessionLocal
from app.routers import auth, canteen, menu, order, payment, delivery_point, notification, category, admin
from app.core.websocket import ws_manager
import app.models  # noqa: F401
from app.routers import upload

Base.metadata.create_all(bind=engine)


async def payment_expiry_worker():
    """Background task — cek expired payments setiap 60 detik"""
    while True:
        await asyncio.sleep(60)
        db = SessionLocal()
        try:
            from app.services.payment_service import expire_pending_payments
            await expire_pending_payments(db)
        finally:
            db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(payment_expiry_worker())
    yield
    task.cancel()


app = FastAPI(
    title="inCampus Food Delivery API",
    description="Backend API untuk sistem pengiriman makanan di dalam kampus.",
    version="1.0.0",
    contact={"name": "inCampus Dev Team"},
    license_info={"name": "MIT"},
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Add production URL here when deploying
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(canteen.router)
app.include_router(menu.router)
app.include_router(delivery_point.router)
app.include_router(order.router)
app.include_router(payment.router)
app.include_router(notification.router)
app.include_router(category.router)
app.include_router(admin.router)
app.include_router(upload.router)


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await ws_manager.connect(user_id, websocket)
    try:
        while True:
            await websocket.receive_text()  # keep alive
    except WebSocketDisconnect:
        ws_manager.disconnect(user_id)


@app.get("/", tags=["Health"])
def root():
    return {
        "service": "inCampus Food Delivery API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
