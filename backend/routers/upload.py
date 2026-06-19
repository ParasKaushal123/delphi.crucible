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
from state.session_store import Phase

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

    # ── Fire pipeline via Band SDK ───────────────────────────
    session_store = request.app.state.session_store
    import uuid
    from band_api.client import get_pm_client
    
    session_id = str(uuid.uuid4())
    session = await session_store.create_session(
        session_id=session_id,
        ticker="PDF",
        main_room_id="",
    )
    session.extracted_text = extracted_text
    session.company_name = name
    await session_store.update_session(session)

    pm_client = get_pm_client()
    try:
        chat_resp = await pm_client.create_chat_room()
        chat_id = chat_resp.get("data", {}).get("id") or chat_resp.get("id")
        
        session.main_room_id = chat_id
        session.phase = Phase.ROLL_CALL
        await session_store.update_session(session)
        
        await session_store.publish_room_message(
            session_id=session_id,
            room_name="Main Room",
            agent="pm-agent",
            content=f"PDF uploaded. Extracting data for **{name}**... Please wait while the agents join.",
        )
        
        # Add all agents to the main room for roll call
        await pm_client.add_participant(chat_id, settings.QUANT_AGENT_ID)
        await pm_client.add_participant(chat_id, settings.BULL_AGENT_ID)
        await pm_client.add_participant(chat_id, settings.BEAR_AGENT_ID)

        # Wait for agents to sync history so this arrives as a live message
        await asyncio.sleep(2)

        # Trigger Roll Call
        await pm_client.send_message(
            chat_id=chat_id,
            content=f"@{settings.QUANT_AGENT_NAME} @{settings.BULL_AGENT_NAME} @{settings.BEAR_AGENT_NAME} Roll call! Please confirm your systems are online.",
            mentions=[
                {"id": settings.QUANT_AGENT_ID, "handle": settings.QUANT_AGENT_NAME},
                {"id": settings.BULL_AGENT_ID, "handle": settings.BULL_AGENT_NAME},
                {"id": settings.BEAR_AGENT_ID, "handle": settings.BEAR_AGENT_NAME},
            ]
        )
    finally:
        await pm_client.close()

    return JSONResponse({
        "status": "started",
        "session_id": session_id,
        "company_name": name,
        "pages_extracted": page_count,
        "characters_extracted": len(extracted_text),
        "message": f"Analyzing {name} ({page_count} pages). Watch the War Room for live updates.",
    })
