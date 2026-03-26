"""
Workflow API - Orchestrates the complete catalog generation pipeline
Phase 9: Upload UI
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from pathlib import Path
from typing import Optional
import asyncio
import httpx

from app.core.config import settings


router = APIRouter(prefix="/api/workflow")


class WorkflowStatus(BaseModel):
    """Current status of workflow execution."""
    upload_id: str
    status: str  # 'pending', 'analyzing', 'merging', 'linking', 'enhancing', 'generating', 'complete', 'error'
    current_step: int
    total_steps: int = 5
    message: str
    error: Optional[str] = None


class WorkflowStartRequest(BaseModel):
    """Request to start workflow."""
    upload_id: str


class WorkflowStartResponse(BaseModel):
    """Response after starting workflow."""
    success: bool
    upload_id: str
    message: str


# Global workflow status storage (in production, use Redis or database)
workflow_statuses: dict[str, WorkflowStatus] = {}


@router.post("/start", response_model=WorkflowStartResponse)
async def start_workflow(
    request: WorkflowStartRequest,
    background_tasks: BackgroundTasks
):
    """
    Start the complete catalog generation workflow.
    
    Executes all steps asynchronously:
    1. CSV Analysis (AI column detection)
    2. Data Fusion (merge CSV files)
    3. Image Linking (match images to products)
    4. Text Enhancement (AI-powered)
    5. HTML Catalog Generation
    
    Args:
        request: WorkflowStartRequest with upload_id
        
    Returns:
        WorkflowStartResponse confirming workflow started
        
    Raises:
        HTTPException 404: Upload not found
        HTTPException 400: Upload already processing
    """
    upload_id = request.upload_id
    upload_dir = Path(settings.upload_dir) / upload_id
    
    # Validate upload exists
    if not upload_dir.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Upload {upload_id} not found"
        )
    
    # Check if workflow is already running
    if upload_id in workflow_statuses:
        if workflow_statuses[upload_id].status not in ['complete', 'error']:
            raise HTTPException(
                status_code=400,
                detail=f"Workflow for {upload_id} is already running"
            )
    
    # Initialize workflow status
    workflow_statuses[upload_id] = WorkflowStatus(
        upload_id=upload_id,
        status='pending',
        current_step=0,
        message='Workflow started'
    )
    
    # Start workflow in background
    background_tasks.add_task(execute_workflow, upload_id, upload_dir)
    
    return WorkflowStartResponse(
        success=True,
        upload_id=upload_id,
        message='Workflow started successfully'
    )


@router.get("/status/{upload_id}", response_model=WorkflowStatus)
async def get_workflow_status(upload_id: str):
    """
    Get current status of workflow execution.
    
    Args:
        upload_id: The upload ID
        
    Returns:
        WorkflowStatus with current progress
        
    Raises:
        HTTPException 404: Workflow not found
    """
    if upload_id not in workflow_statuses:
        # Check if upload exists and is already complete
        upload_dir = Path(settings.upload_dir) / upload_id
        if not upload_dir.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Upload {upload_id} not found"
            )
        
        # Check if catalog already generated
        html_catalog = upload_dir / "html_catalog" / "index.html"
        if html_catalog.exists():
            return WorkflowStatus(
                upload_id=upload_id,
                status='complete',
                current_step=5,
                message='Catalog already generated'
            )
        
        return WorkflowStatus(
            upload_id=upload_id,
            status='pending',
            current_step=0,
            message='Workflow not started'
        )
    
    return workflow_statuses[upload_id]


async def execute_workflow(upload_id: str, upload_dir: Path):
    """
    Execute the complete workflow asynchronously using internal API calls.
    
    This runs in the background and updates workflow_statuses.
    """
    base_url = "http://localhost:8000"  # Internal API
    
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            # Step 1: CSV Analysis
            workflow_statuses[upload_id] = WorkflowStatus(
                upload_id=upload_id,
                status='analyzing',
                current_step=1,
                message='Analyzing CSV files with AI...'
            )
            
            # Find CSV files
            csv_files = list(upload_dir.glob("*.csv"))
            if not csv_files:
                raise Exception("No CSV files found")
            
            # Analyze each CSV
            for csv_file in csv_files:
                response = await client.post(
                    f"{base_url}/api/analysis/csv/{upload_id}/{csv_file.name}"
                )
                if response.status_code != 200:
                    raise Exception(f"CSV analysis failed: {response.text}")
            
            # Step 2: Data Fusion
            workflow_statuses[upload_id] = WorkflowStatus(
                upload_id=upload_id,
                status='merging',
                current_step=2,
                message='Merging product data...'
            )
            
            response = await client.post(
                f"{base_url}/api/merge",
                json={"upload_id": upload_id}
            )
            if response.status_code != 200:
                raise Exception(f"Data merge failed: {response.text}")
            
            # Step 3: Image Linking
            workflow_statuses[upload_id] = WorkflowStatus(
                upload_id=upload_id,
                status='linking',
                current_step=3,
                message='Linking images to products...'
            )
            
            images_dir = upload_dir / "bilder"
            if images_dir.exists() and any(images_dir.iterdir()):
                response = await client.post(
                    f"{base_url}/api/images/link",
                    json={"upload_id": upload_id}
                )
                if response.status_code != 200:
                    raise Exception(f"Image linking failed: {response.text}")
            
            # Step 4: Text Enhancement
            workflow_statuses[upload_id] = WorkflowStatus(
                upload_id=upload_id,
                status='enhancing',
                current_step=4,
                message='Enhancing product texts with AI...'
            )
            
            response = await client.post(
                f"{base_url}/api/texts/enhance",
                json={"upload_id": upload_id}
            )
            if response.status_code != 200:
                raise Exception(f"Text enhancement failed: {response.text}")
            
            # Step 5: HTML Catalog Generation
            workflow_statuses[upload_id] = WorkflowStatus(
                upload_id=upload_id,
                status='generating',
                current_step=5,
                message='Generating HTML catalog...'
            )
            
            response = await client.post(
                f"{base_url}/api/catalog/generate",
                json={"upload_id": upload_id}
            )
            if response.status_code != 200:
                raise Exception(f"Catalog generation failed: {response.text}")
            
            # Complete
            workflow_statuses[upload_id] = WorkflowStatus(
                upload_id=upload_id,
                status='complete',
                current_step=5,
                message='Catalog generation complete!'
            )
        
    except Exception as e:
        workflow_statuses[upload_id] = WorkflowStatus(
            upload_id=upload_id,
            status='error',
            current_step=workflow_statuses.get(upload_id, WorkflowStatus(
                upload_id=upload_id, status='error', current_step=0, message=''
            )).current_step,
            message='Workflow failed',
            error=str(e)
        )
