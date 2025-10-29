# Exposr Trainer - Setup Guide

## Quick Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# Reddit API Credentials (Required)
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_secret
REDDIT_USER_AGENT=Exposr-Trainer/1.0

# Storage Configuration (Optional)
STORAGE_DRIVER=local

# API Authentication (Optional)
TRAINER_API_KEY=your_secret_token

# Exposr-Core Endpoint (Optional)
EXPOSR_CORE_ENDPOINT=http://localhost:8000/detect

# Scheduler Intervals (Optional)
SCRAPE_EVERY_HOURS=12
TRAIN_EVERY_DAYS=7
```

### 3. Configure Reddit API

To get Reddit API credentials:

1. Go to https://www.reddit.com/prefs/apps
2. Click "create app" or "create another app"
3. Select "script" as the type
4. Copy the client ID (under the app name) and secret

### 4. Run the Service

```bash
uvicorn main:app --reload
```

The service will start on `http://localhost:8001`

## Testing the API

### Check Status

```bash
curl http://localhost:8001/status
```

### Trigger Scraping

```bash
curl -X POST http://localhost:8001/scrape
```

If authentication is enabled:

```bash
curl -X POST http://localhost:8001/scrape \
  -H "Authorization: Bearer your_secret_token"
```

### Trigger Training

```bash
curl -X POST http://localhost:8001/train
```

## Directory Structure

After running, you'll see:

```
datasets/
├── images/
│   └── 2025/10/28/
│       └── sample-uuid.jpg
└── meta/
    └── 2025/10/28/
        └── sample-uuid.json

models/
├── registry.json
└── (model versions will be stored here)
```

## Configuration Files

### `config/config.yaml`

Main configuration for the service.

### `config/sources.yaml`

Configure which subreddits to scrape and filtering criteria.

## Troubleshooting

### Reddit API Errors

- Verify your credentials in `.env`
- Check that `REDDIT_USER_AGENT` is set correctly
- Ensure Reddit API limits aren't exceeded

### Storage Issues

- Check that the `datasets/` and `models/` directories are writable
- For S3 storage, ensure AWS credentials are configured

### Import Errors

- Ensure you're running from the project root
- Check that all dependencies are installed

## Next Steps

1. Run initial scrape to build dataset
2. Verify images are being saved correctly
3. Trigger training (mock for MVP)
4. Check model registry for training runs
