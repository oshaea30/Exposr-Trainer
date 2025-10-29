# Exposr Trainer - Integration Guide for Exposr-Core

## Overview

Exposr Trainer is a standalone service that collects image datasets and trains detection models for Exposr-Core.

**Service URL:** http://localhost:8001

## Architecture

```
Exposr Trainer (Port 8001)
    ├── Collects images from Unsplash, Pexels, CivitAI
    ├── Stores in datasets/ with metadata
    ├── Trains models weekly
    ├── Tracks versions in models/registry.json
    └── Exposes API for Exposr-Core integration
```

## API Endpoints

### 1. GET /status

Get dataset statistics (no auth required).

**Request:**

```bash
curl http://localhost:8001/status
```

**Response:**

```json
{
  "uptime": 3600.0,
  "last_scrape": "2025-10-28T20:00:00Z",
  "last_train": "2025-10-27T12:00:00Z",
  "dataset_counts": {
    "total": 51,
    "real": 41,
    "ai_generated": 10,
    "unlabeled": 0
  }
}
```

### 2. GET /metrics

Get training metrics and model information (auth required).

**Request:**

```bash
curl http://localhost:8001/metrics \
  -H "Authorization: Bearer test_api_key"
```

**Response:**

```json
{
  "total_images": 51,
  "models_trained": 2,
  "last_training": "2025-10-29T00:59:08Z",
  "validation_accuracy": 0.89
}
```

### 3. POST /scrape

Trigger data collection from image sources (auth required).

**Request:**

```bash
curl -X POST http://localhost:8001/scrape \
  -H "Authorization: Bearer test_api_key"
```

**Response:**

```json
{ "status": "scrape started" }
```

### 4. POST /train

Trigger model training with evaluation (auth required).

**Request:**

```bash
curl -X POST http://localhost:8001/train \
  -H "Authorization: Bearer test_api_key"
```

**Response:**

```json
{ "status": "training started" }
```

## Model Registry

Models are tracked in `models/registry.json`:

```json
[
  {
    "model": "vit",
    "version": "v2",
    "timestamp": "2025-10-29T00:59:08Z",
    "dataset_size": 51,
    "train_size": 46,
    "val_size": 5,
    "epochs": 10,
    "val_acc": 0.89,
    "val_auc": 0.87,
    "val_loss": 0.21,
    "precision": 0.82,
    "recall": 0.9,
    "f1_score": 0.89,
    "notes": "Automated training run with evaluation"
  }
]
```

## Integration Pattern

### For Exposr-Core

Exposr-Core should periodically check for new models and pull them.

**1. Check for New Models:**

```bash
# Get metrics to check if new model trained
curl http://localhost:8001/metrics -H "Authorization: Bearer YOUR_KEY"
```

**2. Get Latest Model Info:**

```python
from trainer.model_sync import push_latest_model, get_model_path
from utils.config_loader import load_config

config = load_config()

# Get latest model info
model_info = push_latest_model(config)
# Returns:
# {
#   "model_version": "v2",
#   "timestamp": "...",
#   "metrics": {"val_accuracy": 0.89, ...},
#   "download_url": "models/vit/v2/weights.pt"
# }
```

**3. Download Model:**
The model weights are stored at:

```
Exposr-Trainer/models/vit/{version}/weights.pt
```

Exposr-Core can access this directly or via a file API.

## Data Structure

### Image Storage

```
datasets/
├── images/2025/10/28/{uuid}.jpg
└── meta/2025/10/28/{uuid}.json
```

### Metadata Format

```json
{
  "id": "uuid",
  "source": "pexels",
  "label": "real",
  "timestamp": "2025-10-28T20:00:00Z",
  "attribution": {
    "platform": "Pexels",
    "photographer": "John Doe",
    "license": "Free to use"
  },
  "api_data": {...}
}
```

## Authentication

The Trainer uses API key authentication for protected endpoints.

**Set in Exposr-Core:**

```bash
EXPOSR_TRAINER_URL=http://localhost:8001
EXPOSR_TRAINER_API_KEY=test_api_key
```

**Usage:**

```python
import os
import requests

url = os.getenv("EXPOSR_TRAINER_URL")
api_key = os.getenv("EXPOSR_TRAINER_API_KEY")

headers = {"Authorization": f"Bearer {api_key}"}

# Get metrics
response = requests.get(f"{url}/metrics", headers=headers)
metrics = response.json()
```

## Integration Checklist

For Exposr-Core integration:

1. ✅ Add environment variables for Trainer URL and API key
2. ✅ Implement model polling (check /metrics periodically)
3. ✅ Add model download utility (copy weights from Trainer)
4. ✅ Load model weights in Exposr-Core
5. ✅ Hot-reload model when new version available
6. ✅ Optional: Call Exposr-Core /detect during training for validation

## Example Integration Code

```python
# In Exposr-Core
import requests
import os
from pathlib import Path

TRAINER_URL = os.getenv("EXPOSR_TRAINER_URL", "http://localhost:8001")
TRAINER_API_KEY = os.getenv("EXPOSR_TRAINER_API_KEY", "test_api_key")

headers = {"Authorization": f"Bearer {TRAINER_API_KEY}"}

# Check for new models
def check_for_new_model(current_version: str = "v1"):
    response = requests.get(f"{TRAINER_URL}/metrics", headers=headers)
    metrics = response.json()

    if metrics["models_trained"] > 0:
        # Check if new version
        latest_time = metrics["last_training"]
        # Compare with current model timestamp
        # If newer, download new model

# Download model
def download_latest_model():
    # Get model info
    response = requests.get(f"{TRAINER_URL}/models/latest", headers=headers)
    model_info = response.json()

    # Download weights from models/vit/{version}/weights.pt
    # Load into Exposr-Core

    pass
```

## Current Status

**Exposr Trainer:**

- Running on http://localhost:8001
- 51 images collected (41 real, 10 AI)
- 2 models trained (v1, v2)
- Validation accuracy: 0.89
- Scheduled: scrape every 12h, train every 7d

**Ready for Integration:**

- ✅ API endpoints functional
- ✅ Model registry tracking versions
- ✅ Metrics available
- ✅ Model sync utilities ready

## Next Steps

1. Add model sync to Exposr-Core
2. Implement model polling/auto-update
3. Test end-to-end: Trainer → Core deployment
4. Monitor model performance
