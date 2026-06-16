"""
Upload Router — POST /api/analyze/upload
Accepts a 10-K PDF file and runs the full agent pipeline using extracted text.
"""

import asyncio
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import JSONResponse

from tools.pdf_tool import extract_pdf_text, get_pdf_metadata
from agents.pm_agent import run_full_pipeline
from config import settings

router = APIRouter(prefix="/api", tags=["upload"])

MAX_PDF_SIZE_MB = 50
MAX_PDF_SIZE_BYTES = MAX_PDF_SIZE_MB * 1024 * 1024


@router.post("/analyze/upload")
async def analyze_pdf_upload(
    request: Request,
    file: UploadFile = File(...),
    company_name: str = Form(default=""),
):
    """
    Accept a 10-K PDF upload and run the full multi-agent analysis pipeline.

    - Extracts text from the PDF using pdfplumber
    - Passes extracted text directly to the quant agent (skips yfinance)
    - Runs the same Bull / Bear / PM pipeline as the ticker route
    """
    # ── Validate file type ────────────────────────────────────
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    # ── Read file bytes ───────────────────────────────────────
    pdf_bytes = await file.read()

    if len(pdf_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if len(pdf_bytes) > MAX_PDF_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"PDF too large. Maximum size is {MAX_PDF_SIZE_MB}MB.",
        )

    # ── Extract text ──────────────────────────────────────────
    try:
        extracted_text, page_count = await extract_pdf_text(pdf_bytes)
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"Failed to extract text from PDF: {str(e)}"
        )

    if len(extracted_text.strip()) < 200:
        raise HTTPException(
            status_code=422,
            detail="Could not extract readable text from this PDF. It may be a scanned image. Please use a text-based PDF."
        )

    # ── Determine company label ───────────────────────────────
    meta = get_pdf_metadata(pdf_bytes)
    name = (
        company_name.strip()
        or meta.get("title", "")
        or file.filename.replace(".pdf", "").replace("_", " ").replace("-", " ").title()
        or "Unknown Company"
    )

    # ── Fire pipeline in background ───────────────────────────
    session_store = request.app.state.session_store

    asyncio.create_task(
        run_full_pipeline(
            ticker="PDF",
            session_store=session_store,
            band_key="",
            extracted_text=extracted_text,
            company_name=name,
        )
    )

    return JSONResponse({
        "status": "started",
        "company_name": name,
        "pages_extracted": page_count,
        "characters_extracted": len(extracted_text),
        "message": f"Analyzing {name} ({page_count} pages). Watch the War Room for live updates.",
    })
