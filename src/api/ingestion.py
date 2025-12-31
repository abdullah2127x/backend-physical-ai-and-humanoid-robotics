"""
Ingestion API Endpoints - REST API for document ingestion.

Provides endpoints for starting and monitoring content ingestion.
"""

import asyncio
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from pydantic import UUID4

from src.ingestion.models import (
    DocumentStatus,
    IngestionRequest,
    IngestionReport,
    IngestionStatusResponse,
)
from src.ingestion.service import get_ingestion_service

router = APIRouter()

# Track running ingestions
_running_ingestions: dict[UUID, asyncio.Task] = {}


async def run_ingestion_task(report_id: UUID, request: IngestionRequest) -> None:
    """Background task for ingestion."""
    import structlog

    logger = structlog.get_logger(__name__)
    from src.core.config import get_settings

    service = get_ingestion_service()
    settings = get_settings()

    # Resolve path relative to content root
    content_root = settings.content_root
    full_path = content_root / request.path

    logger.info("Ingestion task starting", report_id=str(report_id), request_path=request.path, content_root=str(content_root), full_path=str(full_path), exists=full_path.exists())

    try:
        await service.ingest(
            source_path=str(full_path),
            recursive=request.recursive,
            clear_existing=request.clear_existing,
            report_id=report_id,
        )
    except Exception as e:
        logger.error("Ingestion failed", error=str(e), full_path=str(full_path))


@router.post(
    "/start",
    response_model=IngestionStatusResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start document ingestion",
    description="Begin ingesting documents from the specified path.",
)
async def start_ingestion(
    request: IngestionRequest,
    background_tasks: BackgroundTasks,
) -> IngestionStatusResponse:
    """
    Start ingesting documents from a path.

    Args:
        request: Ingestion configuration
        background_tasks: FastAPI background tasks

    Returns:
        Status response with report ID
    """
    service = get_ingestion_service()

    # Create report first to get ID
    report = IngestionReport(
        source_path=request.path,
        total_files=0,
        processed_files=0,
        status=DocumentStatus.PROCESSING,
    )

    # Start ingestion in background
    task = asyncio.create_task(
        run_ingestion_task(report.id, request),
        name=f"ingestion-{report.id}",
    )
    _running_ingestions[report.id] = task

    return IngestionStatusResponse(
        report_id=report.id,
        status=DocumentStatus.PROCESSING,
        progress={
            "total": 0,
            "processed": 0,
            "percentage": 0.0,
        },
        message=f"Ingestion started for: {request.path}",
    )


@router.get(
    "/status/{report_id}",
    response_model=IngestionStatusResponse,
    summary="Get ingestion status",
    description="Check the status of an ongoing or completed ingestion.",
)
async def get_ingestion_status(report_id: UUID4) -> IngestionStatusResponse:
    """
    Get the status of an ingestion process.

    Args:
        report_id: ID of the ingestion report

    Returns:
        Current status and progress
    """
    service = get_ingestion_service()
    report = service.get_report(report_id)

    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report not found: {report_id}",
        )

    # Calculate progress
    if report.total_files > 0:
        percentage = (report.processed_files / report.total_files) * 100
    else:
        percentage = 0.0

    return IngestionStatusResponse(
        report_id=report.id,
        status=report.status,
        progress={
            "total": report.total_files,
            "processed": report.processed_files,
            "skipped": report.skipped_files,
            "failed": report.failed_files,
            "chunks": report.total_chunks,
            "percentage": round(percentage, 1),
        },
        message=_get_status_message(report),
    )


@router.get(
    "/report/{report_id}",
    response_model=IngestionReport,
    summary="Get full ingestion report",
    description="Get the complete ingestion report with all details.",
)
async def get_ingestion_report(report_id: UUID4) -> IngestionReport:
    """
    Get the full ingestion report.

    Args:
        report_id: ID of the ingestion report

    Returns:
        Complete ingestion report
    """
    service = get_ingestion_service()
    report = service.get_report(report_id)

    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report not found: {report_id}",
        )

    return report


@router.post(
    "/clear",
    status_code=status.HTTP_200_OK,
    summary="Clear collection",
    description="Delete all data from the Qdrant collection.",
)
async def clear_collection() -> dict:
    """
    Clear the Qdrant collection.

    Returns:
        Confirmation message
    """
    from src.core.vector import get_qdrant

    qdrant = get_qdrant()
    await qdrant.connect()
    await qdrant.delete_collection()
    await qdrant.ensure_collection()

    return {
        "message": "Collection cleared successfully",
        "collection": qdrant._collection_name,
    }


def _get_status_message(report: IngestionReport) -> str:
    """Generate a human-readable status message."""
    if report.status.value == "processing":
        return f"Processing {report.processed_files}/{report.total_files} files..."
    elif report.status.value == "completed":
        return f"Completed: {report.processed_files} files, {report.total_chunks} chunks"
    elif report.status.value == "failed":
        return f"Failed: {report.failed_files} files had errors"
    else:
        return f"Status: {report.status.value}"
