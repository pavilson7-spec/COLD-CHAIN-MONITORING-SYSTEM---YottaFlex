from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import time

from app.core.config import settings
from app.core.database import check_db_connection, Base, engine, SessionLocal
from app.core.security import get_password_hash
from app.models.user import User
from app.routes import auth, entities, dashboard, validation, exports

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cold_chain_api")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="High-Integrity Cold Chain Monitoring, Excursion Detection, and Compliance API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow development UI origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# Include Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(dashboard.router, prefix=settings.API_V1_STR)
app.include_router(entities.router, prefix=settings.API_V1_STR)
app.include_router(validation.router, prefix=settings.API_V1_STR)
app.include_router(exports.router, prefix=settings.API_V1_STR)

@app.on_event("startup")
def startup_event():
    logger.info("Initializing Cold Chain Monitoring Backend...")
    # Validate DB connectivity
    if not check_db_connection():
        logger.error("FATAL: Could not connect to PostgreSQL database.")
    else:
        logger.info("Successfully connected to PostgreSQL cold_chain_monitoring_db.")
    
    # Seed default test users if not present
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.username == "admin").first():
            default_admin = User(
                username="admin",
                email="admin@coldchain.internal",
                hashed_password=get_password_hash("AdminSecure2026!"),
                full_name="OT/IT Administrator",
                role="OT/IT Administrator",
                is_active=True
            )
            operator = User(
                username="operator",
                email="operator@coldchain.internal",
                hashed_password=get_password_hash("Operator2026!"),
                full_name="Plant Operator",
                role="Plant Operator",
                is_active=True
            )
            quality = User(
                username="quality",
                email="quality@coldchain.internal",
                hashed_password=get_password_hash("Quality2026!"),
                full_name="Quality Engineer",
                role="Quality Engineer",
                is_active=True
            )
            planner = User(
                username="planner",
                email="planner@coldchain.internal",
                hashed_password=get_password_hash("Planner2026!"),
                full_name="Production Planner",
                role="Production Planner",
                is_active=True
            )
            db.add_all([default_admin, operator, quality, planner])
            db.commit()
            logger.info("Seeded initial role-based users.")
    finally:
        db.close()

@app.get("/")
def root():
    return {
        "project": settings.PROJECT_NAME,
        "status": "online",
        "documentation": "/docs",
        "version": "1.0.0"
    }

@app.get("/health")
def health_check():
    db_ok = check_db_connection()
    return {
        "status": "healthy" if db_ok else "unhealthy",
        "database_connected": db_ok,
        "system_time": time.time()
    }
