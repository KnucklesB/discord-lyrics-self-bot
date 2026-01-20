# 🎵 Discord Lyrics Self-Bot

A sophisticated Discord self-bot that fetches your real-time Spotify playback and displays the lyrics directly in your Discord status. It features an intelligent **Auto-Cache** system to minimize API calls and prevent rate limiting.

> **⚠️ Disclaimer:** Self-bots violate Discord's Terms of Service. Use this at your own risk. This project is for educational purposes only.

---

## ✨ Features

* **Real-time Sync:** Automatically detects your Spotify activity.
* **Lyric Status:** Updates your Discord custom status with the current song's lyrics.
* **Smart Caching:** Local JSON/Database storage for lyrics to avoid redundant API requests.
* **Rate-Limit Protection:** Optimized to stay within Discord and Spotify API boundaries.

## 🛠️ Setup & Credentials

To run this bot, you need to gather specific credentials from Discord and Spotify.

### 1. Discord Token
1. Open Discord in your **Web Browser** (Chrome/Edge).
2. Press `F12` to open Developer Tools.
3. Go to the **Network** tab and refresh the page.
4. Search for `/api` in the filter box.
5. Click on any request and look for the `authorization` header under **Request Headers**.
6. **Copy that value.** This is your Discord Token. **⚠️DANGER: NEVER SHARE YOUR DISCORD TOKEN⚠️**

### 2. Spotify `sp_dc` (For Lyrics)
Since the official Spotify API doesn't provide lyrics easily, we use the `sp_dc` cookie:
1. Open Spotify on your browser and log in.
2. Open Developer Tools (`F12`) -> **Application** tab.
3. Under **Cookies**, select `https://open.spotify.com`.
4. Find the cookie named `sp_dc` and copy its value.

### 3. Spotify Client ID & Secret
1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).
2. Create a new App.
3. **Crucial:** In the app settings, add `http://127.0.0.1:8080` to the **Redirect URIs** list.
4. Copy your **Client ID** and **Client Secret** from the dashboard.

---

## 🚀 Installation

1. **Clone the repo:**
   ```bash
   git clone [https://github.com/your-username/discord-lyrics-self-bot.git](https://github.com/your-username/discord-lyrics-self-bot.git)
   cd discord-lyrics-self-bot
2. **Setup .env file:**
   rename ".env.example" to ".env"
   replace the example informations with yours