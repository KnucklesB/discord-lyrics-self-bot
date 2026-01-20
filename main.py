import time
import requests
from syrics.api import Spotify as LyricsAPI
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import random
import os
from dotenv import load_dotenv # Importe isso
import json
import asyncio

#List of emotes to rotate
EMOTES_SONG =  ["🎶", "🎵", "🎙️","🔈", "🔉", "🔊"]
#Normal statuses when NOT listening to music
DEFAULT_STATUS = [
    ("it works on my machine", "🤷‍♂️"),
    ("refactoring... again", "♻️"),
    ("todo: fix life", "📋"),
    ("git commit -m 'pain'", "📝"),
    ("waiting for the end of file.", "💾"),
    ("process killed.", "💀"),
    ("humanity: deprecated.", "📉"),
    ("out of memory. out of time.", "🧠"),
    ("echo 'help' > /dev/null", "🌌"),
    ("life is a memory leak.", "💧"),
    ("segmentation fault (core dumped)", "💥"),
    ("sudo rm -rf / --no-preserve-root", "🔥"),
    ("compiling... 0%", "⌛"),
    ("404: motivation not found", "🔍"),
    ("while(true) { doNothing(); }", "🔄"),
    ("if (life == hard) { keepGoing(); }", "💪"),
    ("system.out.println('existence');", "💻"),
    ("function sleep() { dream(); }", "😴"),
    ("loading... please wait", "⏳"),
    ("syntax error in life.py", "🐍"),
    ("breaking the build", "🛠️"),
    ("null pointer exception", "❌"),
    ("sudo apt-get install happiness", "😊"),
    ("rm -rf regrets", "🗑️"),
    ("git push origin freedom", "🚀"),
    ("compiling dreams...", "🌠"),
    ("while(!alive) { tryAgain(); }", "🔁"),
    ("system failure: rebooting life", "🔄"),
    ("echo 'stay positive' > /dev/motivation", "🌟"),
    ("if (hope == lost) { findNewHope(); }", "🕊️")
]


#--- Load environment variables ---
load_dotenv()

#--- CONFIGS ---
DISCORD_TOKEN   = os.getenv('DISCORD_TOKEN')    # Discord self-bot token
SPOTIFY_SP_DC   = os.getenv('SPOTIFY_SP_DC')    # Spotify sp_dc cookie value
CLIENT_ID       = os.getenv('CLIENT_ID')        # Spotify Client ID
CLIENT_SECRET   = os.getenv('CLIENT_SECRET')    # Spotify Client Secret

CACHE_FILE      = 'lyrics_cache.json'

# Function to get or refresh Spotify client
def get_spotify_client():
    auth_manager = SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri="http://127.0.0.1:8080/",
        scope="user-read-currently-playing",
        open_browser=False # Prevent opening browser on token refresh
    )
    return spotipy.Spotify(auth_manager=auth_manager)

# Function to change status with random emote
def change_status(text):
    selected_emote = random.choice(EMOTES_SONG)
    url = "https://discord.com/api/v9/users/@me/settings"
    headers = {"Authorization": DISCORD_TOKEN, "Content-Type": "application/json"}
    payload = {"custom_status": {"text": text, "emoji_name": selected_emote}}
    try:
        requests.patch(url, headers=headers, json=payload, timeout=5)
    except:
        pass
# Function to change status with fixed emote
def change_status_with_fixed_emote(text, emote):
    url = "https://discord.com/api/v9/users/@me/settings"
    headers = {"Authorization": DISCORD_TOKEN, "Content-Type": "application/json"}
    payload = {"custom_status": {"text": text, "emoji_name": emote}}
    try:
        requests.patch(url, headers=headers, json=payload, timeout=5)
    except:
        pass
    
# Function to change status to idle mode
async def change_status_idle(self):
    text, emote = random.choice(DEFAULT_STATUS)
    change_status_with_fixed_emote(text, emote)
    await asyncio.sleep(self.idle_count)

# Caching functions
def get_cached_lyrics(song_id):
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            cache = json.load(f)
            return cache.get(song_id)
    return None

# Function to cache lyrics data(modified to store only necessary parts)
def cache_lyrics(song_id, lyrics_data):
    
    lyrics_data_new = {}
    
    if lyrics_data == "":
        lyrics_data_new ={
        "lyrics": {
            "syncType": "NONE",
            "lines": "[]"
            }
        }
    else:
        lyrics_data_new ={
        "lyrics": {
            "syncType": lyrics_data["lyrics"]["syncType"],
            "lines": lyrics_data["lyrics"]["lines"]
            }
        }
    cache = {}
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            cache = json.load(f)
    cache[song_id] = lyrics_data_new
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f)


class SpotifyBot:
    def __init__(self):
        # state variables
        self.last_lyric = ""                                # To track last displayed lyric
        self.current_song_id = ""                           # To track song changes
        self.lyric_sync = []                                # List to hold synced lyrics
        self.search_attempt = False                         # To prevent multiple searches
        self.last_search_timestamp = 0                      # To prevent rapid re-searching
        self.last_api_restart_timestamp = time.time()       # To track when to restart LyricsAPI
        self.show_lyric = True                              # Toggle lyric display
        self.retry_time = 5                                 # seconds to wait before retrying lyric search
        self.playback = {}                                  # To hold current playback info
        self.idle_count = 2                                 # seconds to wait before changing to idle status
        self.l_api = None                                   # Lyrics API instance
        self.sp = None                                      # Spotify client instance
        self.last_api_update_time = time.time()
        
        # Initialize APIs
        try:
            load_dotenv()
            self.l_api = LyricsAPI(SPOTIFY_SP_DC)
            self.sp = get_spotify_client()
        except Exception as e:
            print(f"❌ Error initializing APIs: {e}")
            exit()
            
    # --- LOOP TO SYNC LYRICS WITH PLAYBACK ---
    async def loop_one(self):
        print("Loop status started...")
        while True:
            await asyncio.sleep(0.1)
            # If lyrics are available, sync with current playback time
            if self.playback:
                # get current progress in ms
                base_progress = self.playback['progress_ms']
                # calculate elapsed time since last API update
                time_passed_ms = (time.time() - self.last_api_update_time) * 1300 # Spotify progress can be faster than real time sometimes
                # calculate current progress 
                progress_ms = base_progress + time_passed_ms
                if self.lyric_sync:
                    #progress_ms = self.playback['progress_ms']
                    current_lyric = ""
                    for line in self.lyric_sync:
                        if progress_ms >= int(line['startTimeMs']):
                            current_lyric = line['words']
                            # Handle instrumental lines
                            if current_lyric.strip() == "♪":
                                current_lyric = "♪ Instrumental ♪"
                            # Truncate if too long
                            if len(current_lyric) > 120:
                                current_lyric = current_lyric[:117] + "..."
                        else:
                            break
                    # Update status if lyric changed
                    if current_lyric and current_lyric != self.last_lyric:
                        change_status(current_lyric)
                        self.last_lyric = current_lyric
                        if self.show_lyric:
                            print(f"🎤 [Status] {current_lyric}")
                else:
                    # No lyrics available, show song name
                    change_status_with_fixed_emote(f"Listening to {self.playback['item']['name']}", "🎧")
            else:
                # No song playing, switch to idle status
                await change_status_idle(self)
                
    # --- LOOP TO FETCH PLAYBACK AND LYRICS ---
    async def loop_two(self):
        print("Spotify loop started...")
        while True:
            try:
                await asyncio.sleep(2) # Prevent rate limiting;
                # Your application has reached a rate/request limit. Retry will occur after: 41722 s <--- NOT GOOD
                self.playback = self.sp.current_user_playing_track() # get current playback info
                # playback = sp.currently_playing() # Alternative method
                if self.playback and self.playback.get('is_playing'):
                    self.last_api_update_time = time.time()
                    # If song changed, reset everything for new search
                    if self.playback['item']['id'] != self.current_song_id:
                        track_name = self.playback['item']['name']
                        artist_name = self.playback['item']['artists'][0]['name']
                        print(f"\n🎵 Now playing: {track_name} by {artist_name}")
                        self.current_song_id = self.playback['item']['id']
                        self.lyric_sync = []
                        self.search_attempt = False
                        self.last_search_timestamp = 0
                        self.last_lyric = ""
                        change_status_with_fixed_emote(f"Listening to {track_name}", "🎧")             
                    # Try to load lyrics if not already loaded
                    if not self.lyric_sync and not self.search_attempt:
                        try:
                            print("🔍 Searching for lyrics...")
                            # Check cache first
                            self.lyric_data = get_cached_lyrics(self.current_song_id)
                            
                            if self.lyric_data:
                                print("🔍 Found lyrics in cache.")
                                # Check for No Lyrics case
                                if self.lyric_data['lyrics']['syncType'] == "NONE":
                                    print("❌ No lyrics found for this song in cache.")
                                    self.lyric_sync = []
                                # Check for Lyrics not synced case
                                if self.lyric_data['lyrics']['syncType'] == "UNSYNCED":
                                    print("❌ song has unsynced lyrics in cache.")
                                    self.lyric_sync = []
                                # Check for Synced lyrics case
                                if self.lyric_data['lyrics']['syncType'] == "LINE_SYNCED":
                                    self.lyric_sync = self.lyric_data['lyrics']['lines']
                                    print("✅ Lyrics loaded from cache.")
                            else:
                                print("🔍 Searching for lyrics in API...")
                                try:
                                    lyric_data = self.l_api.get_lyrics(self.current_song_id)
                                    
                                    # If no lyrics found, try restarting the API instance after 1800 seconds(half hour)
                                    if lyric_data is None and ((time.time() - self.last_api_restart_timestamp) > 1800):
                                        #restart l_api instance and try again
                                        self.l_api = LyricsAPI(SPOTIFY_SP_DC)
                                        lyric_data = self.l_api.get_lyrics(self.current_song_id)
                                        print("🔄 Restarted Lyrics API.")
                                        self.last_api_restart_timestamp = time.time()
                                        self.lyric_sync = []
                                        self.search_attempt = False
                                    # Final check
                                    else:
                                        if lyric_data is None:
                                            print("❌ No lyrics found for this song in API.")
                                            cache_lyrics(self.current_song_id, "")  # Cache the absence of lyrics
                                        else:
                                            cache_lyrics(self.current_song_id, lyric_data)
                                            self.lyric_sync = lyric_data['lyrics']['lines']
                                            print("✅ Lyrics found and cached.")
                                except Exception as e:
                                    print(f"❌ Error fetching lyrics from API: {e}")
                                    lyric_data = None
                        except Exception as e:
                            print(e)
                            self.lyric_sync = []
                            print("❌ Failed to load lyrics.")
                        self.search_attempt = True
                        self.last_search_timestamp = time.time()
                else:
                    self.playback = None
            except Exception as e:
                print(f"❌ Error in main loop: {e}")
                await asyncio.sleep(self.retry_time)  # Wait before retrying in case of error
    async def run(self):
        print("🤖 Bot is running...")
        await asyncio.gather(self.loop_one(), self.loop_two())
        
                
            
            
bot = SpotifyBot()
try:
    asyncio.run(bot.run())
except KeyboardInterrupt:
    print("🤖 Bot stopped by user.")