from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)

# IMPORTANT:
# If your files are inside app/
# keep app.ingest and app.chat
#
# If all files are in the same folder,
# change imports to:
#
# from ingest import router as ingest_router
# from chat import router as chat_router
#
# For now keep these:

from app.ingest import router as ingest_router
from app.chat import router as chat_router

app = FastAPI(
    title="BrowserBaba API",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(
    ingest_router,
    prefix="/api",
    tags=["Ingest"],
)

app.include_router(
    chat_router,
    prefix="/api",
    tags=["Chat"],
)

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("====================================")
    logger.info("BrowserBaba Backend Started")
    logger.info("Docs: http://127.0.0.1:8000/docs")
    logger.info("Health: http://127.0.0.1:8000/health")
    logger.info("====================================")

# Health check
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "browserbaba-backend"
    }

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "BrowserBaba API Running"
    }
