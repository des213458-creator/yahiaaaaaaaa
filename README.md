# Railway m3u8 Telegram Bot (simple)

This repo contains a Telegram bot that downloads .m3u8 streams and sends MP4 back to the user.

Deploy steps:
1. Push this repo to GitHub.
2. Sign in to Railway and select "Deploy from GitHub repo".
3. Add env variables: BOT_TOKEN (required), USE_N=1 (optional).
4. (Optional) Add Build Command: bash install.sh
5. Deploy and test the bot on Telegram.

Notes:
- If you want N_m3u8DL-RE to be used, either upload the binary to repo root or let install.sh download it during build.
- Telegram has file size limits for uploads.
