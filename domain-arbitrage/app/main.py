"""FastAPI application entry point.

Run with::

    uvicorn app.main:app --reload

The dashboard at ``/`` is deliberately minimal - a single server-rendered page.
The requirement was decision quality over UI polish, and every number on that
page is a link into the audit trail rather than a chart.
"""

from __future__ import annotations

import logging

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.routes import router
from app.config import REPO_ROOT
from app.db.base import get_db
from app.db.init_db import SchemaDriftError, init_db
from app.models.analysis import PipelineRun
from app.scoring.config import get_scoring_config
from app.services.paper_portfolio import performance
from app.services.report import build_report

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(name)s: %(message)s")

@asynccontextmanager
async def lifespan(_app: FastAPI):
    try:
        init_db()
    except SchemaDriftError as exc:
        logging.getLogger(__name__).error("%s", exc)
        raise
    cfg = get_scoring_config()
    logging.getLogger(__name__).info(
        "scoring config %s (calibrated=%s)", cfg.stamp, cfg.calibrated)
    yield


app = FastAPI(
    lifespan=lifespan,
    title="Domain Arbitrage Intelligence Engine",
    version="0.1.0",
    description=(
        "Research and ranking engine for identifying domains priced materially "
        "below their likely end-user value.\n\n"
        "**All valuations and probabilities are produced by an UNCALIBRATED V0 "
        "heuristic.** No coefficient has been fitted to observed sales. Use the "
        "paper portfolio to accumulate outcomes before risking capital."),
)
app.include_router(router)

templates = Jinja2Templates(directory=str(REPO_ROOT / "app" / "templates"))


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, limit: int = 25,
              db: Session = Depends(get_db)) -> HTMLResponse:
    report = build_report(db, limit=limit)
    runs = db.execute(select(PipelineRun).order_by(PipelineRun.id.desc())
                      .limit(5)).scalars().all()
    cfg = get_scoring_config()
    return templates.TemplateResponse(
        request=request, name="dashboard.html",
        context={"report": report, "runs": runs, "cfg": cfg,
                 "performance": performance(db)})
