# ==================== main.py ====================
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from routes.kyc_routes import router as kyc_router
from database import init_db

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG
)

# Initialize database
try:
    init_db()
except Exception as e:
    print(f"⚠️ Database initialization error: {e}")
    print("Make sure PostgreSQL is running and credentials are correct in .env")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(kyc_router)

@app.get("/")
async def root():
    return {"message": "KYC Verification API", "version": settings.VERSION, "database": "PostgreSQL"}

@app.get("/health")
async def health_check():
    return {"status": "ok", "database": "connected"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)