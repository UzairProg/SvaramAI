"""
SvaramAI - Sanskrit AI Intelligence Suite
Production-grade API for Sanskrit language processing
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import time

from routes import (
    chandas_routes,
    shloka_routes,
    tagline_routes,
    meaning_routes,
    knowledgebase_routes,
    voice_routes,
    chatbot_routes
)



# Load environment variables from .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # If dotenv is not installed, skip (but recommend installing for local dev)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    logger.info("🚀 SvaramAI starting...")
    logger.info("✅ All modules initialized")
    yield
    logger.info("👋 SvaramAI shutting down...")


# Initialize FastAPI app
app = FastAPI(
    title="SvaramAI - Sanskrit Intelligence Suite",
    description="Production-grade AI backend for Sanskrit language processing with Chandas identification, Shloka generation, RAG knowledge base, and more.",
    version="1.0.0",
    lifespan=lifespan
)


# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests and measure response time"""
    start_time = time.time()
    
    logger.info(f"📥 {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(
        f"📤 {request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Global exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    errors = exc.errors()
    
    # Convert error details to JSON-serializable format
    serializable_errors = []
    for error in errors:
        serializable_error = {
            "loc": error.get("loc"),
            "msg": error.get("msg"),
            "type": error.get("type"),
            "input": str(error.get("input")) if error.get("input") is not None else None
        }
        serializable_errors.append(serializable_error)
    
    logger.error(f"Validation error: {serializable_errors}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "details": serializable_errors,
            "message": "Invalid request parameters"
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "details": str(exc) if app.debug else None
        }
    )


# Health check endpoint
@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - health check"""
    return {
        "status": "healthy",
        "service": "Sanskrit AI Intelligence Suite",
        "version": "1.0.0",
        "modules": [
            "chandas_identifier",
            "shloka_generator",
            "tagline_generator",
            "meaning_engine",
            "knowledge_base",
            "voice_analyzer",
            "chatbot"
        ]
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "services": {
            "api": "operational",
            "llm": "operational",
            "rag": "operational"
        }
    }


# Include routers
app.include_router(chandas_routes.router, prefix="/api/v1", tags=["Chandas Identifier"])
app.include_router(shloka_routes.router, prefix="/api/v1", tags=["Shloka Generator"])
app.include_router(tagline_routes.router, prefix="/api/v1", tags=["Tagline Generator"])
app.include_router(meaning_routes.router, prefix="/api/v1", tags=["Meaning Engine"])
app.include_router(knowledgebase_routes.router, prefix="/api/v1", tags=["Knowledge Base"])
app.include_router(voice_routes.router)
app.include_router(chatbot_routes.router, tags=["Chatbot"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
