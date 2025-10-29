# Quick Start - Refactored Trainer

## Test Without API Keys (API Error Expected)

The service is running but will show API errors without credentials.
This is expected.

```bash
# Test the scraper (will show API errors without keys)
curl -X POST http://localhost:8001/scrape \
  -H "Authorization: Bearer test_api_key"

# Check status
curl http://localhost:8001/status
```

## Get API Keys (Optional)

1. **Unsplash:** https://unsplash.com/developers - Create app, get Access Key
2. **Pexels:** https://www.pexels.com/api/ - Sign up, get API key
3. **Update .env:**
   ```bash
   UNSPLASH_ACCESS_KEY=your_key
   PEXELS_API_KEY=your_key
   ```

## Restart With API Keys

```bash
pkill -f uvicorn
uvicorn main:app --host 0.0.0.0 --port 8001 &
```

Then test again - should now fetch images!
