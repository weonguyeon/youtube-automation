"""FastAPI 앱 — YouTube 자동화 대시보드 백엔드"""

from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# 프로젝트 루트를 sys.path에 추가 (pipeline 임포트용)
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.config import OUTPUT_DIR
from web.backend.routes import jobs, presets, settings, videos
from web.backend.services.job_manager import JobManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    yield
    # shutdown
    JobManager.get_instance().shutdown()


app = FastAPI(
    title="YouTube Automation Dashboard",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우트
app.include_router(jobs.router)
app.include_router(presets.router)
app.include_router(videos.router)
app.include_router(settings.router)

# output/ 정적 파일 서빙
if OUTPUT_DIR.exists():
    app.mount("/output", StaticFiles(directory=str(OUTPUT_DIR)), name="output")


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "0.1.0"}
