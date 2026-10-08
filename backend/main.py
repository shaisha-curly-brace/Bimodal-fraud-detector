"""
backend/main.py

FastAPI entry point for Multimodal Fraud Detection System.
Mounts API routes and serves the static cybersecurity dashboard frontend.
"""

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.config import settings
from backend.api.routes import router as api_router
from backend.utils.logger import logger


def verify_models_present():
    """Validates that all required model weight files exist before starting server."""
    text_model_file = settings.TEXT_MODEL_DIR / "text_vectorizer.joblib"
    url_model_file = settings.URL_MODEL_DIR / "url_classifier.joblib"
    fusion_model_file = settings.FUSION_MODEL_DIR / "fusion_classifier.joblib"

    missing = []
    if not text_model_file.exists():
        missing.append(f"Text Model ({text_model_file})")
    if not url_model_file.exists():
        missing.append(f"URL Model ({url_model_file})")
    if not fusion_model_file.exists():
        missing.append(f"Fusion Model ({fusion_model_file})")

    if missing:
        error_msg = (
            "\n" + "=" * 70 + "\n"
            " [FATAL ERROR] Model weights missing!\n"
            f" Missing: {', '.join(missing)}\n"
            " Please train models first by running:\n"
            "     python run.py --train\n"
            + "=" * 70 + "\n"
        )
        logger.error(error_msg)
        raise RuntimeError(
            "Model weights not found. Please train models first using 'python run.py --train' before launching the server."
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Verifying model weights availability...")
    verify_models_present()
    logger.info("All model weights successfully verified and loaded.")
    logger.info("Multimodal Fraud Detection Server starting up...")
    yield
    logger.info("Multimodal Fraud Detection Server shutting down...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Multimodal Fraud Detection (Text + URL) with XAI Explanations",
    lifespan=lifespan
)

# Enable CORS for local development and web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Router at both /api and /api/v1 for flexible routing
app.include_router(api_router, prefix="/api")
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# Root dashboard endpoint
frontend_dir = settings.STATIC_DIR
index_file = frontend_dir / "index.html"

@app.get("/", include_in_schema=False)
async def serve_index():
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "Multimodal Fraud Detection API is running.", "docs": "/docs"}

# Serve Frontend static assets
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
else:
    logger.warning(f"Frontend directory not found at {frontend_dir}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=False)
