"""
Gastor Backend API
==================

FastAPI backend for the Gastor trading platform.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import market, strategies, optimizer, results, glossary, live
from core.database import engine, Base
from core import models  # Important to register models

# Create Tables
Base.metadata.create_all(bind=engine)

# Create app
app = FastAPI(
    title="Gastor API",
    description="API REST para a plataforma de trading Gastor",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS - Permite Cloudflare Pages
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",           # Dev local
        "http://localhost",                # Docker prod local
        "http://localhost:80",             # Docker prod local explicit
        "https://*.pages.dev",             # Cloudflare Pages
        "https://gastor.pages.dev",        # Produção (ajustar nome)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registra rotas
app.include_router(market.router, prefix="/api/market", tags=["Market"])
app.include_router(strategies.router, prefix="/api/strategies", tags=["Strategies"])
app.include_router(optimizer.router, prefix="/api/optimizer", tags=["Optimizer"])
app.include_router(results.router, prefix="/api/results", tags=["Results"])
app.include_router(glossary.router, prefix="/api/glossary", tags=["Glossary"])
app.include_router(live.router, prefix="/api/live", tags=["Live Trading"])


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": "1.0.0"}


@app.get("/")
async def root():
    """Root endpoint - redirect to docs."""
    return {"message": "Gastor API", "docs": "/docs"}
