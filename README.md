# Exposr Trainer

Background service for scraping, labeling, and training Exposr detection models.

## Overview

The Exposr Trainer is a standalone service that:

- Collects images from Reddit (and other sources)
- Labels them using Exposr-Core detection
- Stores them in structured datasets with deduplication
- Periodically retrains detection models
- Provides API endpoints for manual triggers

## Quick Start

### Installation

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set up environment variables (copy and configure):

```bash
cp .env.example .env
# Edit .env with your credentials
```

Required environment variables:

- `REDDIT_CLIENT_ID` - Reddit API client ID
- `REDDIT_CLIENT_SECRET` - Reddit API client secret
- `REDDIT_USER_AGENT` - Reddit user agent string
- `TRAINER_API_KEY` - API key for authentication (optional)
- `EXPOSR_CORE_ENDPOINT` - Exposr-Core API endpoint (optional)

### Running the Service

Start the service:

```bash
uvicorn main:app --reload
```

The service will:

- Start the FastAPI server on `http://localhost:8001`
- Schedule scraping jobs every 12 hours (configurable)
- Schedule training jobs every 7 days (configurable)

## Configuration

Configuration is managed through YAML files and environment variables.

### `config/config.yaml`

Main configuration file for storage, scheduling, and API settings.

### `config/sources.yaml`

Source configuration for scrapers (subreddits, filters, etc.).

### Environment Variables

Environment variables override YAML settings:

- `STORAGE_DRIVER` - Storage driver (`local` or `s3`)
- `SCRAPE_EVERY_HOURS` - Scraping interval in hours
- `TRAIN_EVERY_DAYS` - Training interval in days

## API Endpoints

### `GET /status`

Get service status including uptime, last run times, and dataset statistics.

Response:

```json
{
  "uptime": 3600.0,
  "last_scrape": "2025-10-28T10:00:00Z",
  "last_train": "2025-10-25T12:00:00Z",
  "dataset_counts": {
    "total": 1500,
    "ai_generated": 800,
    "real": 700,
    "unlabeled": 0
  }
}
```

### `POST /scrape`

Manually trigger a scraping job. Requires API key if configured.

Response:

```json
{
  "status": "scrape started"
}
```

### `POST /train`

Manually trigger a training job. Requires API key if configured.

Response:

```json
{
  "status": "training started"
}
```

## Directory Structure

```
/exposr-trainer/
├── main.py                    # FastAPI application
├── config/
│   ├── config.yaml           # Main configuration
│   └── sources.yaml          # Source configuration
├── scraper/
│   ├── reddit_scraper.py     # Reddit scraper
│   └── image_cleaner.py      # Image validation
├── labeler/
│   ├── auto_labeler.py       # Auto-labeling
│   └── exposr_core_client.py # Exposr-Core integration
├── dataset/
│   ├── dataset_manager.py    # Dataset management
│   └── storage.py            # Storage abstraction
├── trainer/
│   ├── train_vit.py          # Training script
│   └── model_registry.py     # Model registry
├── api/
│   └── routes.py             # API routes
└── utils/
    └── config_loader.py      # Configuration loader
```

## Storage

### Local Storage (Default)

Images and metadata are stored in:

- `datasets/images/{yyyy/mm/dd}/{uuid}.jpg`
- `datasets/meta/{yyyy/mm/dd}/{uuid}.json`

Model versions are stored in:

- `models/vit/{version}/weights.pt`
- `models/registry.json`

### S3 Storage (Future)

S3Storage is stubbed and ready for implementation. Configure via:

```bash
STORAGE_DRIVER=s3
```

## Scraping

The Reddit scraper collects images from configured subreddits:

- Filters by minimum score
- Filters by post age
- Validates image format and size
- Deduplicates by SHA-256 hash
- Extracts post metadata

## Labeling

Images are automatically labeled using:

- Exposr-Core detection API (primary)
- Placeholder support for additional detectors (Hive, Optic)

Labels are stored in metadata:

- `label`: "ai_generated" or "real"
- `confidence`: Detection confidence score
- `detectors`: Object with detector scores

## Training

Training runs are tracked in the model registry (`models/registry.json`):

```json
{
  "model": "vit",
  "version": "v1",
  "timestamp": "2025-10-28T10:00:00Z",
  "dataset_size": 1500,
  "val_acc": 0.89,
  "val_auc": 0.92,
  "notes": "Training on Reddit dataset"
}
```

## Logging

Logs are written to stdout and include:

- Scraping job start/complete
- Training job start/complete
- Sample counts and statistics
- Errors and warnings

## Development

### Running Tests

```bash
# Scrape and label a few samples
curl -X POST http://localhost:8001/scrape

# Check status
curl http://localhost:8001/status

# Trigger training
curl -X POST http://localhost:8001/train
```

### Adding New Scrapers

Implement scraper in `scraper/` following RedditScraper pattern.

### Adding New Detectors

Implement detector client in `labeler/` and integrate in `auto_labeler.py`.

## Authentication

To enable authentication, set `TRAINER_API_KEY` environment variable:

```bash
export TRAINER_API_KEY=your_secret_token
```

API calls to POST endpoints require:

```
Authorization: Bearer your_secret_token
```

## Future Extensions

- Twitter/X scraper
- News feed scraper
- Full S3Storage implementation
- Celery migration for distributed tasks
- Advanced training with hyperparameter tuning
- Model evaluation suite
- Automatic model deployment to Exposr-Core

## License

MIT
