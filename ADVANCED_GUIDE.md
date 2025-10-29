# Exposr Trainer - Advanced Guide

## Overview

Exposr Trainer is a complete ML training pipeline that collects diverse image datasets, trains detection models, and syncs with Exposr-Engine. This guide covers advanced configuration, customization, and extensions.

## Data Flow

```
Image APIs → FetcherManager → DatasetManager → Trainer → ModelRegistry → Exposr-Core
             (Unsplash,      (deduplication,  (evaluation) (versioning)  (deployment)
              Pexels,        storage)
              CivitAI)
```

## Architecture

### Fetcher System

The fetcher system is modular and extensible:

```python
# Base fetcher interface
class BaseFetcher(ABC):
    @abstractmethod
    def fetch_images(self, limit: int) -> List[Tuple[bytes, dict]]

    @abstractmethod
    def get_source_name(self) -> str
```

**Adding New Sources:**

1. Create new fetcher in `scraper/`:

   ```python
   from scraper.base_fetcher import BaseFetcher

   class MySourceFetcher(BaseFetcher):
       def __init__(self, config: dict):
           self.api_key = os.getenv("MYSOURCE_API_KEY")

       async def fetch_images(self, limit: int = 25):
           # Fetch images from API
           # Return List[Tuple[bytes, dict]]
           pass

       def get_source_name(self) -> str:
           return "mysource"
   ```

2. Register in `scraper/fetcher_manager.py`:

   ```python
   from scraper.mysource_fetcher import MySourceFetcher

   # In _initialize_fetchers():
   elif name == "mysource":
       fetchers.append(MySourceFetcher(self.config))
   ```

3. Add to `config/sources.yaml`:
   ```yaml
   sources:
     - name: mysource
       enabled: true
       label: "real" # or "ai"
   ```

### Dataset Management

Datasets are stored with metadata and deduplication:

```
datasets/
├── images/2025/10/28/{uuid}.jpg
├── meta/2025/10/28/{uuid}.json
└── dedupe.db  (SQLite for hash-based dedup)
```

**Metadata Schema:**

```json
{
  "id": "uuid",
  "source": "pexels",
  "label": "real",
  "confidence": null,
  "timestamp": "2025-10-28T20:00:00Z",
  "hash": "sha256",
  "attribution": {
    "platform": "Pexels",
    "photographer": "John Doe",
    "license": "Free to use",
    "url": "..."
  },
  "api_data": {
    "photo_id": 123,
    "width": 1920,
    "height": 1080
  }
}
```

### Model Training

Training runs are scheduled weekly and tracked in the registry:

**Training Flow:**

1. Check dataset size (requires 50+ samples)
2. Split into train/validation (90/10)
3. Train model (mock for MVP)
4. Evaluate on validation set
5. Register metrics in `models/registry.json`

**Model Registry:**

```json
{
  "model": "vit",
  "version": "v2",
  "timestamp": "2025-10-29T00:59:08Z",
  "dataset_size": 51,
  "train_size": 46,
  "val_size": 5,
  "val_acc": 0.89,
  "val_auc": 0.87,
  "val_loss": 0.23,
  "precision": 0.82,
  "recall": 0.85
}
```

## API Endpoints

### `GET /status`

Service status with dataset counts.

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

### `GET /metrics`

Training metrics and model statistics.

**Response:**

```json
{
  "total_images": 51,
  "models_trained": 2,
  "last_training": "2025-10-29T00:59:08Z",
  "validation_accuracy": 0.89
}
```

### `POST /scrape`

Trigger ingestion from all enabled sources.

**Request:**

```bash
curl -X POST http://localhost:8001/scrape \
  -H "Authorization: Bearer your_api_key"
```

### `POST /train`

Trigger training job with evaluation.

**Request:**

```bash
curl -X POST http://localhost:8001/train \
  -H "Authorization: Bearer your_api_key"
```

## Configuration

### Environment Variables

```bash
# Image APIs
UNSPLASH_ACCESS_KEY=your_key
PEXELS_API_KEY=your_key
CIVITAI_API_URL=https://civitai.com/api/v1

# Security
TRAINER_API_KEY=your_secret_token

# Exposr-Core Integration
EXPOSR_CORE_ENDPOINT=http://localhost:8000/api/v1/analyze

# Storage
STORAGE_DRIVER=local  # or "s3"

# Scheduler
SCRAPE_EVERY_HOURS=12
TRAIN_EVERY_DAYS=7
```

### Sources Configuration

`config/sources.yaml`:

```yaml
reddit:
  enabled: false # Disabled due to IP blocking

sources:
  - name: unsplash
    enabled: true
    label: "real"
    queries:
      - "portrait photography"
      - "nature photography"
    limit_per_query: 10
    rate_limit_per_hour: 50

  - name: pexels
    enabled: true
    label: "real"
    queries:
      - "fashion"
      - "lifestyle"
    limit_per_query: 10
    rate_limit_per_hour: 200

  - name: civitai
    enabled: true
    label: "ai"
    queries:
      - "characters"
      - "landscapes"
    limit_per_query: 10
    rate_limit_per_hour: 100
```

## Exposr-Core Integration

### Model Sync Function

```python
from trainer.model_sync import push_latest_model, get_model_path

# Get latest model info for Exposr-Core
model_info = push_latest_model(config)
# Returns: {
#   "model_version": "v2",
#   "timestamp": "...",
#   "metrics": {...},
#   "download_url": "models/vit/v2/weights.pt"
# }
```

**Exposr-Core Integration Pattern:**

1. Exposr-Core calls `GET /metrics` to check for new models
2. If new model available, calls `GET /models/latest`
3. Downloads model weights from `download_url`
4. Loads and deploys new model

## Extending the System

### Adding New Image Sources

See "Fetcher System" section above for complete guide.

### Implementing Real Training

Replace mock in `trainer/train_vit.py` with actual PyTorch training:

```python
def train_vit(dataset_path: str, output_dir: str, epochs: int = 10):
    # Load dataset
    dataset = load_image_dataset(dataset_path)

    # Create model
    model = timm.create_model("vit_base_patch16_224", pretrained=True)

    # Train
    trainer = Trainer(model, dataset)
    metrics = trainer.fit(epochs=epochs)

    # Save weights
    torch.save(model.state_dict(), f"{output_dir}/weights.pt")

    return metrics
```

### Adding S3 Storage

Implement `S3Storage` in `dataset/storage.py`:

```python
class S3Storage(StorageDriver):
    def __init__(self, config):
        import boto3
        self.s3 = boto3.client('s3')
        self.bucket = config["storage"]["s3_bucket"]

    def save_image(self, image_bytes: bytes, relative_path: str) -> str:
        self.s3.put_object(
            Bucket=self.bucket,
            Key=f"images/{relative_path}",
            Body=image_bytes
        )
        return f"s3://{self.bucket}/images/{relative_path}"
```

Then set `STORAGE_DRIVER=s3` in `.env`.

## Security

All POST and GET (with auth) endpoints require `TRAINER_API_KEY`:

```bash
# Set in .env
TRAINER_API_KEY=your_secret_token

# Use in requests
Authorization: Bearer your_secret_token
```

## Monitoring

**Check Service Status:**

```bash
curl http://localhost:8001/status
```

**Check Metrics:**

```bash
curl http://localhost:8001/metrics \
  -H "Authorization: Bearer your_api_key"
```

**View Logs:**

```bash
tail -f logs/trainer.log
```

**Check Collected Images:**

```bash
find datasets/images -name "*.jpg" | wc -l
```

## Troubleshooting

**No images collected:**

- Check API keys in `.env`
- Verify SSL certificates (may need `ssl=False` in fetchers)
- Check rate limits on API provider

**Training fails:**

- Ensure dataset has 50+ images
- Check logs for specific errors
- Verify model registry is writable

**Missing labels:**

- Ensure fetchers set `label` in metadata
- Check that labeler doesn't overwrite fetcher labels

## Next Steps

1. Implement real PyTorch training pipeline
2. Add S3 storage for production
3. Integrate with Exposr-Core auto-deployment
4. Add user upload support (placeholder ready)
5. Monitor model performance over time
