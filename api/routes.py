"""FastAPI routes for the trainer API."""
import os
import time
import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, status
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Global state
router = APIRouter()
app_state: Dict[str, Any] = {
    "start_time": time.time(),
    "last_scrape": None,
    "last_train": None,
    "scraping": False,
    "training": False
}

# Import job functions (defined in main.py)
# These will be set during app initialization
scrape_job_func = None
train_job_func = None
dataset_manager = None


class StatusResponse(BaseModel):
    """Status response model."""
    uptime: float
    last_scrape: str | None
    last_train: str | None
    dataset_counts: Dict[str, int]


class MetricsResponse(BaseModel):
    """Metrics response model."""
    total_images: int
    models_trained: int
    last_training: str | None
    validation_accuracy: float | None


def verify_api_key(authorization: str | None = Header(None)) -> bool:
    """Verify API key from Authorization header.
    
    Args:
        authorization: Authorization header value
        
    Returns:
        True if authorized
    """
    api_key = os.getenv("TRAINER_API_KEY")
    
    if api_key and not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )
    
    if api_key and authorization:
        expected = f"Bearer {api_key}"
        if authorization != expected:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
    
    return True


@router.get("/status", response_model=StatusResponse)
async def get_status():
    """Get service status.
    
    Returns:
        Status information including uptime and dataset counts
    """
    uptime = time.time() - app_state["start_time"]
    
    # Get dataset statistics
    counts = {"total": 0, "ai_generated": 0, "real": 0, "unlabeled": 0}
    if dataset_manager:
        counts = dataset_manager.get_dataset_stats()
    
    return {
        "uptime": uptime,
        "last_scrape": app_state["last_scrape"],
        "last_train": app_state["last_train"],
        "dataset_counts": counts
    }


@router.post("/scrape")
async def trigger_scrape(
    background_tasks: BackgroundTasks,
    _: bool = Header(verify_api_key)
):
    """Trigger a scraping job.
    
    Args:
        background_tasks: FastAPI background tasks
        
    Returns:
        Response indicating scrape was started
    """
    if app_state["scraping"]:
        return {"status": "scrape already in progress"}
    
    if scrape_job_func:
        app_state["scraping"] = True
        background_tasks.add_task(execute_scrape_job)
        return {"status": "scrape started"}
    else:
        return {"status": "scraper not configured"}


@router.post("/train")
async def trigger_train(
    background_tasks: BackgroundTasks,
    _: bool = Header(verify_api_key)
):
    """Trigger a training job.
    
    Args:
        background_tasks: FastAPI background tasks
        
    Returns:
        Response indicating training was started
    """
    if app_state["training"]:
        return {"status": "training already in progress"}
    
    if train_job_func:
        app_state["training"] = True
        background_tasks.add_task(execute_train_job)
        return {"status": "training started"}
    else:
        return {"status": "trainer not configured"}


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    _: bool = Header(verify_api_key)
):
    """Get training metrics and statistics.
    
    Returns:
        Training metrics including accuracy, dataset size, etc.
    """
    # Import model registry
    from trainer.model_registry import ModelRegistry
    from utils.config_loader import load_config
    
    config = load_config()
    registry = ModelRegistry(config)
    
    # Get models
    models = registry.list_models()
    latest = registry.get_latest("vit")
    
    # Get dataset manager stats
    stats = {"total": 0, "real": 0, "ai_generated": 0}
    if dataset_manager:
        stats = dataset_manager.get_dataset_stats()
    
    return {
        "total_images": stats.get("total", 0),
        "models_trained": len(models),
        "last_training": latest.get("timestamp") if latest else None,
        "validation_accuracy": latest.get("val_acc") if latest else None
    }


async def execute_scrape_job():
    """Execute the scraping job."""
    try:
        logger.info("Starting scrape job")
        if scrape_job_func:
            await scrape_job_func()
        app_state["last_scrape"] = datetime.utcnow().isoformat()
        logger.info("Scrape job complete")
    except Exception as e:
        logger.error(f"Error in scrape job: {e}")
    finally:
        app_state["scraping"] = False


async def execute_train_job():
    """Execute the training job."""
    try:
        logger.info("Starting training job")
        if train_job_func:
            await train_job_func()
        app_state["last_train"] = datetime.utcnow().isoformat()
        logger.info("Training job complete")
    except Exception as e:
        logger.error(f"Error in training job: {e}")
    finally:
        app_state["training"] = False


def set_scrape_job(func):
    """Set the scrape job function."""
    global scrape_job_func
    scrape_job_func = func


def set_train_job(func):
    """Set the train job function."""
    global train_job_func
    train_job_func = func


def set_dataset_manager(dm):
    """Set the dataset manager."""
    global dataset_manager
    dataset_manager = dm

