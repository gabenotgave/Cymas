"""FastAPI application entrypoint for Cymas API."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import metrics
from api.routers import analysis

app = FastAPI(title="Cymas API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
app.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
