from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app.routers import auth, canteen, menu, order, payment, delivery_point, notification, category, admin
import app.models  # noqa: F401 — ensure all models registered before create_all

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="inCampus Food Delivery API",
    description="Backend API untuk sistem pengiriman makanan di dalam kampus.",
    version="1.0.0",
    contact={"name": "inCampus Dev Team"},
    license_info={"name": "MIT"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
