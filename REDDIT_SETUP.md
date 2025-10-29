# Reddit API Setup for Google SSO Users

## Option 1: Create App Password (Recommended)

1. Go to https://www.reddit.com/prefs/apps
2. Click on your app "Exposr-Scraper"
3. Look for "personal access token" or "app password" option
4. Generate a new token for this app
5. Use that token as your password in .env

## Option 2: Use OAuth Tokens Instead

Modify scraper to use OAuth2 refresh tokens instead of username/password

## Option 3: Create a Dedicated Reddit Account

Create a separate Reddit account (not tied to Google SSO) specifically for the API

