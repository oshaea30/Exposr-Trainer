# Exposr Trainer - Quick Start

## ✅ Service is Running!

The Exposr Trainer is currently running on **http://localhost:8001**

## Test the API

```bash
# Check status
curl http://localhost:8001/status

# Trigger scraping (needs real Reddit credentials)
curl -X POST http://localhost:8001/scrape \
  -H "Authorization: Bearer test_api_key"

# Trigger training
curl -X POST http://localhost:8001/train \
  -H "Authorization: Bearer test_api_key"

# View logs
tail -f logs/trainer.log
```

## Current Status

From the logs, we can see:

- ✅ Service started successfully
- ✅ APScheduler is configured
- ✅ Scraping job ran (but needs valid Reddit API credentials)
- ✅ Training job ran successfully and created model version v1
- ✅ Model registered in `models/registry.json`

## What's Working

1. **FastAPI server** - Running on port 8001
2. **APScheduler** - Automatically schedules scrape every 12h, train every 7d
3. **API endpoints** - /status, /scrape, /train all functional
4. **Model registry** - Tracking training runs
5. **Storage** - Local storage ready for datasets and models

## To Add Real Reddit Credentials

Edit the `.env` file with your actual Reddit API credentials:

```bash
REDDIT_CLIENT_ID=your_real_client_id
REDDIT_CLIENT_SECRET=your_real_secret
```

Then restart the service.

## Service Management

```bash
# Stop the service
pkill -f "uvicorn main:app"

# Restart the service
uvicorn main:app --host 0.0.0.0 --port 8001 &

# View logs
tail -f logs/trainer.log
```

## Next Steps

1. Add real Reddit API credentials to `.env`
2. Let the scraper collect images over time
3. Build dataset by triggering scraping manually or waiting for scheduled runs
4. Training will run automatically every 7 days
5. Check model registry to see training history
