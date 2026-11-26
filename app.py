"""FastAPI server for the Cryptographic Systems Simulator."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from benchmark import run_benchmark_suite
from ciphers import CipherValidationError, run_cipher


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title="Cryptographic Systems Simulator",
    version="1.0.0",
    description="Interactive classical cipher visualizer and micro-benchmarking API.",
)


class TransformRequest(BaseModel):
    algorithm: Literal["caesar", "playfair", "vigenere", "rail_fence", "columnar"]
    mode: Literal["encrypt", "decrypt"] = "encrypt"
    text: str = Field(..., min_length=1, max_length=50000)
    key: Any


class BenchmarkRequest(BaseModel):
    runs: int = Field(default=20, ge=1, le=50)
    custom_text: str | None = Field(default=None, max_length=50000)
    selected_algorithm: str = "vigenere"
    selected_key: Any = None


@app.post("/api/transform")
def transform_endpoint(payload: TransformRequest) -> dict[str, Any]:
    """Encrypt or decrypt text and return step-by-step visual trace data."""
    try:
        return run_cipher(
            algorithm=payload.algorithm,
            text=payload.text,
            key=payload.key,
            mode=payload.mode,
            include_trace=True,
        )
    except CipherValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/benchmark")
def benchmark_endpoint(payload: BenchmarkRequest | None = None) -> dict[str, Any]:
    """Run micro-benchmarks across 100B, 1KB, 10KB, and 50KB payloads."""
    req = payload or BenchmarkRequest()
    return run_benchmark_suite(
        runs=req.runs,
        custom_text=req.custom_text,
        selected_algorithm=req.selected_algorithm,
        selected_key=req.selected_key,
    )


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def serve_index() -> FileResponse:
    return FileResponse(str(STATIC_DIR / "index.html"))
