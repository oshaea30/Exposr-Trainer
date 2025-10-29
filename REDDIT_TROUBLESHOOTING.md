# Reddit API 401 Error Troubleshooting

## Current Situation
- Getting 401 errors with Reddit script app
- App type: "personal use script"  
- Using only client_id and client_secret

## Possible Issues

1. **Reddit API Changes**: Reddit may have deprecated simple client credentials authentication
2. **App Activation**: New apps can take 24-48 hours to fully activate
3. **Authentication Method**: Script apps may now require:
   - OAuth2 token flow
   - OR username/password + app credentials

## Solutions to Try

### Option A: Test Without PRAW
```bash
curl -X GET "https://www.reddit.com/r/pics/hot.json?limit=1" \
  -H "User-Agent: Exposr-Trainer/1.0"
```
(Public API, no auth needed)

### Option B: Try Different Auth Mode
Use username/password authentication properly with script type.

### Option C: Wait 24-48 Hours
New Reddit apps can take time to activate.

### Option D: Check Reddit App Settings
Ensure the app shows as "active" in Reddit's developer portal.
