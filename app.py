""" 
   _____ _                   _  _____                  
  / ____| |                 | |/ ____|                 
 | |    | |__   ___  _ __ __| | (___  _   _ _ __   ___ 
 | |    | '_ \ / _ \| '__/ _` |\___ \| | | | '_ \ / __|
 | |____| | | | (_) | | | (_| |____) | |_| | | | | (__ 
  \_____|_| |_|\___/|_|  \__,_|_____/ \__, |_| |_|\___|
                                       __/ |           
                                      |___/            
by Simon Roedig (Mediainformatics @LMU Munich)
Bachelor's Thesis (WS 2023/2024)
"""

######## IMPORTS ########
import eventlet
eventlet.monkey_patch()

import html
import json
import math
import os
import re
import requests
import datetime
import atexit
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, send_from_directory, session, g
from fuzzywuzzy import fuzz
from icecream import ic
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from spotipy import SpotifyOAuth
from spotipy.exceptions import SpotifyException
import spotipy
import sqlite3
import pathlib
import string
import time
import random
import threading

# Fix SSL recursion issue
import ssl
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    # Legacy Python that doesn't verify HTTPS certificates by default
    pass
else:
    # Handle target environment that doesn't support HTTPS verification
    ssl._create_default_https_context = _create_unverified_https_context

######## FLASK ########
app = Flask(__name__)
app.config.from_object(__name__)
app.config.update(
  SESSION_COOKIE_NAME='spotify-login-session',
  SECRET_KEY=os.environ['FLASK_SECRET_KEY'],
  SESSION_COOKIE_SECURE=True,
  SESSION_COOKIE_HTTPONLY=True,
  SESSION_COOKIE_SAMESITE='Lax',
)
#CORS(app, resources={r"/*": {"origins": ["https://chordsync.io", "https://chordsync.onrender.com", "http://192.168.2.100:5000/"]}})

# https://stackoverflow.com/questions/20035101/why-does-my-javascript-code-receive-a-no-access-control-allow-origin-header-i

######## DATABASE ########
DATABASE_LYRICS = 'lyrics_data.db'
DATABASE_UE = 'ue_data.db'

def get_database(db_name):
    db = getattr(g, '_database_' + db_name, None)
    if db is None:
        db = g._database = sqlite3.connect(db_name)
        db.row_factory = sqlite3.Row
    return db

def close_database(db_name, exception):
    db = getattr(g, '_database_' + db_name, None)
    if db is not None:
        db.close()

def init_database(db_name, table_name, columns):
    with app.app_context():
        db = get_database(db_name)
        cursor = db.cursor()
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {table_name} (
                {', '.join(columns)}
            )
        ''')
        db.commit()

@app.teardown_appcontext
def teardown_db(exception):
    close_database('lyrics', exception)
    close_database('ue', exception)

# Initialization
init_database(DATABASE_LYRICS, 'lyrics_db', [
    'track_id TEXT PRIMARY KEY',
    'artist_name TEXT',
    'track_name TEXT',
    'save_timestamp TEXT',
    'original_json TEXT'
])

init_database(DATABASE_UE, 'ue_db', [
    'track_id TEXT PRIMARY KEY',
    'artist_name TEXT',
    'track_name TEXT',
    'save_timestamp TEXT',
    'complete_source_code TEXT',
    'complete_source_code_link TEXT',
    'complete_source_code_found INTEGER',
    'result_index INTEGER'
])


######## .env ########
load_dotenv()
dev_or_prod = os.getenv("DEV_OR_PROD") # either "DEVELOPMENT" or "PRODUCTION"
lyrics_api_source = os.getenv("LYRICS_API_SOURCE") # either "REST" or "SELFMADE"
log_on_off = os.getenv("LOG_ON_OFF") # either "ON" or "OFF"
print(f"dev_or_prod: {dev_or_prod}")
print(f"lyrics_api_source: {lyrics_api_source}")
print(f"log_on_off: {log_on_off}")


######## LOGGING ########
timestamp = datetime.datetime.now().strftime("%d_%m_%Y__%H_%M_%S")
log_file_path = f'logs/log__{timestamp}.txt'
song_in_log = 248

wrote_block_1 = ""
wrote_block_2 = ""
wrote_block_3 = ""
wrote_block_4 = ""

if (dev_or_prod == "DEVELOPMENT" and log_on_off == "ON"):
    with open(log_file_path, 'a') as file:
        file.write(f"Playlist Name: Easy Songs to Learn on Guitar\n")
        file.write(f"Playlist Created by: GuitarCatMatt\n")
        file.write(f"Playlist Likes: 1.353\n")
        file.write(f"Playlist Timestamp: {timestamp}\n")
        file.write(f"-> Link: https://open.spotify.com/playlist/5hrQcqeuQCVu3tWbl8T8Y9?si=f80e9e2d6cea41e4\n")
                
                
######## SELFMADE SPOTIFY LYRICS ########
if (lyrics_api_source == "SELFMADE"):
    from spotify_lyrics import SpotifyLyrics
    sp_dc_cookie = os.getenv("SP_DC_COOKIE")
    getLyrics = SpotifyLyrics(sp_dc_cookie)
    
######## LRCLIB SPOTIFY LYRICS ########
if (lyrics_api_source == "LRCLIB"):
    from lrclib_lyrics import LRCLIBLyrics
    getLyrics = LRCLIBLyrics()




######## WEB SOCKET ########
#socketio = SocketIO(app, cors_allowed_origins=["https://chordsync.io", "https://chordsync.onrender.com", 'http://192.168.2.100:5000/'])
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*")


######## SPOTIFY API ########
if (dev_or_prod == "PRODUCTION"):
    print("In Production")
    spotify_client_id = os.getenv("SPOTIFY_CLIENT_ID")
    spotify_client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    spotify_redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI")
elif (dev_or_prod == "DEVELOPMENT"):
    print("In Development")
    spotify_client_id = os.getenv("SPOTIFY_CLIENT_ID_LOCAL")
    spotify_client_secret = os.getenv("SPOTIFY_CLIENT_SECRET_LOCAL")
    spotify_redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI_LOCAL")

spotify_scope = 'user-modify-playback-state,user-read-playback-state'
sp_oauth = SpotifyOAuth(client_id=spotify_client_id, client_secret=spotify_client_secret, redirect_uri=spotify_redirect_uri, scope=spotify_scope, show_dialog=True, cache_path=None)

# Add this function to create the SpotifyOAuth object
def create_spotify_oauth():
    return SpotifyOAuth(
        client_id=spotify_client_id,
        client_secret=spotify_client_secret,
        redirect_uri=spotify_redirect_uri,
        scope=spotify_scope,
        show_dialog=True,
        cache_path=None
    )


######## GOOGLE API ########
google_api_key = os.getenv("GOOGLE_API_KEY")
google_search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")


######## GLOBAL VARIABLES ########
complete_source_code = ""
complete_source_code_link = ""
complete_source_code_found = 0

guitar_tuning = 0
guitar_capo = 0

synced_lyrics_json = 0
synced_lyrics_tupel_array = []

main_chords_body = ""

found_musixmatch_lyrics = 0
musixmatch_lyrics_is_linesynced = 0

spotify_error = 0

is_logged_in = False

spotify_user_name = ""

track_bpm = 0
track_key = 0

sync_ratio_percentage = "0%"

previous_spotify_volume = 0


######## HTTP ROUTES ########
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.root_path, 'static/favicon.png', mimetype='image/vnd.microsoft.icon')

@app.route('/')
def index():
    global is_logged_in
    token_info = session.get('token_info', {})
    if token_info == {}:
        is_logged_in = False
    else:
        is_logged_in = True
        
    token_info = refresh_token()
    if token_info != 0:
        spotify = spotipy.Spotify(auth=token_info['access_token'])
        spotify_user_name = spotify.current_user()['display_name']
        image = spotify.current_user()['images']
        spotify_user_image = image[0]['url'] if image else ""

    else:
        spotify_user_name = ""
        spotify_user_image = ""

    return render_template('index.html', album_cover_url="", track_name="Track", artist_name="Artist", minutes=0, seconds=00, 
                           guitar_tuning="E A D G B E", guitar_capo="0", main_chords_body="", complete_source_code_link='javascript:void(0)', 
                           is_logged_in=is_logged_in, spotify_user_name=spotify_user_name, spotify_user_image=spotify_user_image, dev_or_prod=dev_or_prod, log_on_off=log_on_off)

@app.route('/login')
def login():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/logout')
def logout():
    global is_logged_in
    # Clearing the session data
    session.clear()  
    
    # Delete the Spotipy cache file
    cache_file = '.cache'
    if os.path.exists(cache_file):
        os.remove(cache_file)
        
    is_logged_in = False
    return redirect('/')  

@app.route('/callback')
def callback():
    logout()
    global is_logged_in
    error = request.args.get('error')
    code = request.args.get('code')
    
    if error:
        # User declined the authorization
        is_logged_in = False
    elif code:
        # User accepted the authorization, proceed to get the token
        is_logged_in = True
        # Create the SpotifyOAuth object
        sp_oauth = create_spotify_oauth()
        
        try:
            # Fix for the deprecation warning - explicitly set as_dict=True
            token_info = sp_oauth.get_access_token(code, as_dict=True)
            session['token_info'] = token_info
        except Exception as e:
            ic(f"Error in callback: {e}")
            is_logged_in = False
    else:
        # No code and no error, handle according to your application's logic
        is_logged_in = False

    return redirect('/')

def refresh_token():
    global is_logged_in
    token_info = session.get('token_info', {})
    if token_info == {}:
        is_logged_in = False
        return 0
    if sp_oauth.is_token_expired(token_info):
        is_logged_in = True
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        session['token_info'] = token_info
    return token_info


######## WEBSOCKET ROUTES ########
@socketio.on('connect')
def handleConnect():
    print('WebSocket: Client (JavaScript) connected to Server (Python)')
    
@socketio.on('trackDynamicDataRequest')
def handleDynamicDataRequest():
    emit('trackDynamicDataResponse', getTrackDynamicData())
    
@socketio.on('trackStaticDataRequest')
def handleStaticDataRequest(align="left"):
    emit('trackStaticDataResponse', getTrackStaticData(align))
    
@socketio.on('nextSpotifyTrack')
def nextSpotifyTrack():
    try:
        token_info = refresh_token()
        if token_info == 0:
            return redirect('/')
        
        spotify = spotipy.Spotify(auth=token_info['access_token'])
        spotify.next_track()
        return redirect('/')
    
    except SpotifyException as e:
        if e.http_status == 403 and "PREMIUM_REQUIRED" in str(e):
            emit('error_message', {'message': 'Error: Spotify Premium required for this action.'})
        else:
            print(f'Error: {e}')
    except Exception as e:
        print(f'Error: {e}')
        return redirect('/')
    
@socketio.on('previousSpotifyTrack')
def previousSpotifyTrack():
    try:
        token_info = refresh_token()
        if token_info == 0:
            return redirect('/')

        spotify = spotipy.Spotify(auth=token_info['access_token'])
        spotify.previous_track()
        return redirect('/')
    
    except SpotifyException as e:
        if e.http_status == 403 and "PREMIUM_REQUIRED" in str(e):
            emit('error_message', {'message': 'Error: Spotify Premium required for this action.'})
        else:
            print(f'Error: {e}')
    except Exception as e:
        print(f'Error: {e}')
        return redirect('/')

@socketio.on('playPauseSpotifyTrack')
def playPauseSpotifyTrack():
    try:
        token_info = refresh_token()
        if token_info == 0:
            return redirect('/')
        
        spotify = spotipy.Spotify(auth=token_info['access_token'])
        current_track = spotify.current_playback()
        is_playing = current_track['is_playing']
        if is_playing:
            spotify.pause_playback()
        else:
            spotify.start_playback()
        return redirect('/')
    
    except SpotifyException as e:
        if e.http_status == 403 and "PREMIUM_REQUIRED" in str(e):
            emit('error_message', {'message': 'Error: Spotify Premium required for this action.'})
        else:
            print(f'Error: {e}')
    except Exception as e:
        print(f'Error: {e}')
        return redirect('/')

@socketio.on('increaseVolumeSpotify')
def increaseVolumeSpotify():
    try:
        token_info = refresh_token()
        if token_info == 0:
            return redirect('/')

        spotify = spotipy.Spotify(auth=token_info['access_token'])
        current_track = spotify.current_playback()
        current_volume = current_track['device']['volume_percent']

        # Increase the volume by 10% (you can adjust this value)
        new_volume = min(current_volume + 10, 100)

        spotify.volume(volume_percent=new_volume)
        return redirect('/')
    
    except SpotifyException as e:
        if e.http_status == 403 and "PREMIUM_REQUIRED" in str(e):
            emit('error_message', {'message': 'Error: Spotify Premium required for this action.'})
        else:
            print(f'Error: {e}')
    except Exception as e:
        print(f'Error: {e}')
        return redirect('/')

@socketio.on('decreaseVolumeSpotify')
def decreaseVolumeSpotify():
    try:
        token_info = refresh_token()
        if token_info == 0:
            return redirect('/')

        spotify = spotipy.Spotify(auth=token_info['access_token'])
        current_track = spotify.current_playback()
        current_volume = current_track['device']['volume_percent']

        # Decrease the volume by 10% (you can adjust this value)
        new_volume = max(current_volume - 10, 0)

        spotify.volume(volume_percent=new_volume)
        return redirect('/')
    
    except SpotifyException as e:
        if e.http_status == 403 and "PREMIUM_REQUIRED" in str(e):
            emit('error_message', {'message': 'Error: Spotify Premium required for this action.'})
        else:
            print(f'Error: {e}')
    except Exception as e:
        print(f'Error: {e}')
        return redirect('/')

@socketio.on('muteSpotifyTrack')
def muteSpotifyTrack():
    global previous_spotify_volume
    try:
        token_info = refresh_token()
        if token_info == 0:
            return redirect('/')

        spotify = spotipy.Spotify(auth=token_info['access_token'])
        current_track = spotify.current_playback()
        current_volume = current_track['device']['volume_percent']
        
        if (current_volume != 0):
            previous_spotify_volume = current_volume
            
        elif (current_volume == 0):
            spotify.volume(volume_percent=previous_spotify_volume)
            return redirect('/')

        # Decrease the volume by 10% (you can adjust this value)
        new_volume = max(current_volume - current_volume, 0)

        spotify.volume(volume_percent=new_volume)
        return redirect('/')
    
    except SpotifyException as e:
        if e.http_status == 403 and "PREMIUM_REQUIRED" in str(e):
            emit('error_message', {'message': 'Error: Spotify Premium required for this action.'})
        else:
            print(f'Error: {e}')
    except Exception as e:
        print(f'Error: {e}')
        return redirect('/')
   
@socketio.on('toggleShuffleState')
def toggleShuffleState():
    try:
        token_info = refresh_token()
        if token_info == 0:
            return redirect('/')

        spotify = spotipy.Spotify(auth=token_info['access_token'])
        current_playback = spotify.current_playback()
        current_shuffle_state = current_playback['shuffle_state']

        # Toggle the shuffle state
        new_shuffle_state = not current_shuffle_state

        spotify.shuffle(state=new_shuffle_state)
        return redirect('/')

    except SpotifyException as e:
        if e.http_status == 403 and "PREMIUM_REQUIRED" in str(e):
            emit('error_message', {'message': 'Error: Spotify Premium required for this action.'})
        else:
            print(f'Error: {e}')
    except Exception as e:
        print(f'Error: {e}')
        return redirect('/')

@socketio.on('toggleRepeatState')
def toggleRepeatState():
    try:
        token_info = refresh_token()
        if token_info == 0:
            return redirect('/')

        spotify = spotipy.Spotify(auth=token_info['access_token'])
        current_playback = spotify.current_playback()
        current_repeat_state = current_playback['repeat_state']

        # Toggle the repeat state
        if current_repeat_state == 'off':
            new_repeat_state = 'track'  # Repeat current track
        elif current_repeat_state == 'track':
            new_repeat_state = 'context'  # Repeat current context (playlist or album)
        else:
            new_repeat_state = 'off'  # Turn off repeat

        spotify.repeat(state=new_repeat_state)
        return redirect('/')

    except SpotifyException as e:
        if e.http_status == 403 and "PREMIUM_REQUIRED" in str(e):
            emit('error_message', {'message': 'Error: Spotify Premium required for this action.'})
        else:
            print(f'Error: {e}')
    except Exception as e:
        print(f'Error: {e}')
        return redirect('/')
    
@socketio.on('jumpInsideTrack')
def jumpInsideTrack(ms):
    try:
        token_info = refresh_token()
        if token_info == 0:
            return redirect('/')

        spotify = spotipy.Spotify(auth=token_info['access_token'])
        spotify.seek_track(ms)
        return redirect('/')
    
    except SpotifyException as e:
        if e.http_status == 403 and "PREMIUM_REQUIRED" in str(e):
            emit('error_message', {'message': 'Error: Spotify Premium required for this action.'})
        else:
            print(f'Error: {e}')
    except Exception as e:
        print(f'Error: {e}')
        return redirect('/')

@socketio.on('/songBackwards')
def seek(progress_ms, wind_lenght_ms):
    try:
        token_info = refresh_token()
        if token_info == 0:
            return redirect('/')

        print("SONG BACKWARDS")
        new_progress_ms = int(progress_ms) - int(wind_lenght_ms)
        if new_progress_ms < 0:
            new_progress_ms = 0
        spotify = spotipy.Spotify(auth=token_info['access_token'])
        spotify.seek_track(new_progress_ms)
        return redirect('/')
    
    except SpotifyException as e:
        if e.http_status == 403 and "PREMIUM_REQUIRED" in str(e):
            emit('error_message', {'message': 'Error: Spotify Premium required for this action.'})
        else:
            print(f'Error: {e}')
    except Exception as e:
        print(f'Error: {e}')
        return redirect('/')
    
@socketio.on('/songForwards')
def seek(progress_ms, track_duration_ms, wind_lenght_ms):
    try:
        token_info = refresh_token()
        if token_info == 0:
            return redirect('/')

        new_progress_ms = int(progress_ms) + int(wind_lenght_ms)
        if new_progress_ms > track_duration_ms:
            new_progress_ms = progress_ms
        spotify = spotipy.Spotify(auth=token_info['access_token'])
        spotify.seek_track(new_progress_ms)
        return redirect('/')
    
    except SpotifyException as e:
        if e.http_status == 403 and "PREMIUM_REQUIRED" in str(e):
            emit('error_message', {'message': 'Error: Spotify Premium required for this action.'})
        else:
            print(f'Error: {e}')
    except Exception as e:
        print(f'Error: {e}')
        return redirect('/')


# Called by WebSocket - returns object with parameters that change during the song 
def getTrackDynamicData():    
    token_info = refresh_token()
    if token_info == 0:
        return {
            'track_id': "0",
            'progress_ms': 0,
            'current_time': "0:00",
            'play_or_pause': "False",
            'current_volume': 0,
            'current_shuffle_state': "False",
            'current_repeat_state': 'off'
        }
    spotify = spotipy.Spotify(auth=token_info['access_token'])
    
    try:
        current_track = spotify.current_playback()
    except SpotifyException as e:
        current_track = None
        ic(f'Error: {e}')
        
    if current_track is None:
        return {
            'track_id': "0",
            'progress_ms': 0,
            'current_time': "0:00",
            'play_or_pause': "False",
            'current_volume': 0,
            'current_shuffle_state': "False",
            'current_repeat_state': 'off'
        }
    
    track_id = current_track['item']['id']
    progress_ms = current_track['progress_ms']
    minutes, seconds = divmod(progress_ms / 1000, 60)
    is_playing = str(current_track['is_playing'])
    current_volume = current_track['device']['volume_percent']
    current_shuffle_state = current_track['shuffle_state']
    current_repeat_state = current_track['repeat_state']
    
    return {
            'track_id': track_id,
            'progress_ms': progress_ms,
            'current_time': f"{int(minutes)}:{int(seconds):02d}",
            'play_or_pause': is_playing,
            'current_volume': current_volume,
            'current_shuffle_state': current_shuffle_state,
            'current_repeat_state': current_repeat_state
        }

# Called by Websocket - returns object with parameters that DON'T change during the song 
def getTrackStaticData(align):        
    global complete_source_code 
    global complete_source_code_link
    global complete_source_code_found
    
    global guitar_tuning
    global guitar_capo
    
    global synced_lyrics_json
    global synced_lyrics_tupel_array
    
    global main_chords_body 
    
    global spotify_error
    
    global track_bpm
    global track_key
    
    global sync_ratio_percentage
    
    global song_in_log
    
    global wrote_block_1
    global wrote_block_2
    global wrote_block_3
    
    token_info = refresh_token()
    if token_info == 0:
        complete_source_code_link = ""
        complete_source_code_found = 0
        
        guitar_tuning = "E A D G B E"
        guitar_capo = "0"
                
        main_chords_body  = "Welcome to ChordSync. <br> Login to start."
        
        found_musixmatch_lyrics = 0
        musixmatch_lyrics_is_linesynced = 0
        
        track_bpm = 0
        track_key = 0
        
        sync_ratio_percentage = "0%"
        
        spotify_error = 1
        
        return {
            'track_name': "Track",
            'artist_name': "Artist",
            'track_duration_ms': "",
            'track_duration_m_and_s': "0:00",
            'album_cover_url': "",
            'guitar_tuning': guitar_tuning,
            'guitar_capo': guitar_capo,
            'main_chords_body': main_chords_body,
            'complete_source_code_link': "javascript:void(0)",
            'complete_source_code_found': complete_source_code_found,
            'musixmatch_lyrics_is_linesynced': musixmatch_lyrics_is_linesynced,
            'found_musixmatch_lyrics': found_musixmatch_lyrics,
            'spotify_error': spotify_error,
            'track_bpm': track_bpm,
            'sync_ratio_percentage': sync_ratio_percentage,
            'track_key': track_key
        }
        
    spotify = spotipy.Spotify(auth=token_info['access_token'])
    
    try:
        current_track = spotify.current_playback()
    except SpotifyException as e:
        current_track = None
        ic(f'Error: {e}')
    
    if current_track is not None:
        track_id = current_track['item']['id']
        track_name = current_track['item']['name']
        artist_name = current_track['item']['artists'][0]['name']
        track_duration_ms = current_track["item"]["duration_ms"]
        minutes, seconds = divmod(track_duration_ms / 1000, 60)
        album_cover_url = current_track['item']['album']['images'][0]['url']
        
        ####
        # Get audio features for the current track
        try:
            audio_features = spotify.audio_features([track_id])
            if audio_features:
                track_bpm = round(audio_features[0]['tempo'])
                
                track_key_value = audio_features[0]['key'] # Range: -1 - 11: https://en.wikipedia.org/wiki/Pitch_class
                
                key_number_array = [-1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
                key_tonal_array = ["0", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
                key_tonal = key_tonal_array[key_number_array.index(track_key_value)]
                
                track_key_major_or_minor_value = audio_features[0]['mode'] # Major is represented by 1 and minor is 0
                track_key_major_or_minor = "" if track_key_major_or_minor_value == 1 else "m"
                
                track_key = f"{key_tonal}{track_key_major_or_minor}"
            else:
                ic('Audio features not available for this track.')
        except SpotifyException as e:
            ic(f'Error fetching audio features: {e}')
        ###
        
        
        if (dev_or_prod == "DEVELOPMENT" and log_on_off == "ON" and wrote_block_1 != track_id):
            with open(log_file_path, 'a') as file:
                wrote_block_1 = track_id
                
                file.write(f"\n")
                file.write(f"-------------------------\n")
                file.write(f"SONG: {song_in_log}\n")
                file.write(f"TRACK ID: {track_id}\n")
                file.write(f"TRACK NAME: {track_name}\n")
                file.write(f"ARTIST NAME: {artist_name}\n")
                file.write(f"-----\n")
                song_in_log += 1
    
        
        spotify_error = 0
        
        complete_source_code, complete_source_code_link, complete_source_code_found, result_index = googleChordsForDB(track_name, artist_name, track_id)
        main_chords_body = complete_source_code;
        
        if (dev_or_prod == "DEVELOPMENT" and log_on_off == "ON" and wrote_block_2 != track_id):
            with open(log_file_path, 'a') as file:
                wrote_block_2 = track_id
                
                file.write(f"FOUND ULTIMATE GUITAR CHORDS: {'YES' if complete_source_code_found else 'NO'}\n")
                file.write(f"ULTIMATE GUITAR URL: {complete_source_code_link}\n")
                file.write(f"GOOGLE RESULT INDEX: {result_index}\n")
                file.write(f"-----\n")
                
        
        if complete_source_code_found == 1:
            guitar_tuning = extractTuning(complete_source_code)
            guitar_capo = extractCapo(complete_source_code)
        
            main_chords_body = extractMainChordsBody(complete_source_code, align)
            
            synced_lyrics_json, found_musixmatch_lyrics, musixmatch_lyrics_is_linesynced = getSyncedLyricsJson(track_id, artist_name, track_name)
            
            if (dev_or_prod == "DEVELOPMENT" and log_on_off == "ON" and wrote_block_3 != track_id):
                with open(log_file_path, 'a') as file:
                    wrote_block_3 = track_id
                    
                    file.write(f"FOUND LYRICS: {'YES' if found_musixmatch_lyrics else 'NO'}\n")
                    file.write(f"LYRICS ARE LINE SYNCED: {'YES' if musixmatch_lyrics_is_linesynced else 'NO'}\n")
                    file.write(f"-----\n")
            
            # Happy Path: Chords and synced lyrics found
            if (found_musixmatch_lyrics == 1 and musixmatch_lyrics_is_linesynced == 1):
                synced_lyrics_tupel_array = parseSyncedLyricsJsonToTupelArray(synced_lyrics_json)

                ### Main Algorithm
                main_chords_body, error_syncing = insertTimestampsToMainChordsBody(synced_lyrics_tupel_array, main_chords_body, track_duration_ms, track_id)
                
                # If sync below treshold, regard as unsyncable (like no lyrics found)
                if error_syncing:
                    print(error_syncing)
                    sync_ratio_percentage = "0"
                    found_musixmatch_lyrics = 0
                    musixmatch_lyrics_is_linesynced = 0
                    return {
                        'track_name': track_name,
                        'artist_name': artist_name,
                        'track_duration_ms': track_duration_ms,
                        'track_duration_m_and_s': f"{int(minutes)}:{int(seconds):02d}",
                        'album_cover_url': album_cover_url,
                        'guitar_tuning': guitar_tuning,
                        'guitar_capo': guitar_capo,
                        'main_chords_body': main_chords_body,
                        'complete_source_code_link': complete_source_code_link,
                        'complete_source_code_found': complete_source_code_found,
                        'musixmatch_lyrics_is_linesynced': musixmatch_lyrics_is_linesynced,
                        'found_musixmatch_lyrics': found_musixmatch_lyrics,
                        'spotify_error': spotify_error,
                        'track_bpm': track_bpm,
                        'sync_ratio_percentage': sync_ratio_percentage,
                        'track_key': track_key
                    }
                
                return {
                    'track_name': track_name,
                    'artist_name': artist_name,
                    'track_duration_ms': track_duration_ms,
                    'track_duration_m_and_s': f"{int(minutes)}:{int(seconds):02d}",
                    'album_cover_url': album_cover_url,
                    'guitar_tuning': guitar_tuning,
                    'guitar_capo': guitar_capo,
                    'main_chords_body': main_chords_body,
                    'complete_source_code_link': complete_source_code_link,
                    'complete_source_code_found': complete_source_code_found,
                    'musixmatch_lyrics_is_linesynced': musixmatch_lyrics_is_linesynced,
                    'found_musixmatch_lyrics': found_musixmatch_lyrics,
                    'spotify_error': spotify_error,
                    'track_bpm': track_bpm,
                    'sync_ratio_percentage': sync_ratio_percentage,
                    'track_key': track_key
                }
            
            # Found chords but no synced lyrics
            else:
                sync_ratio_percentage = "0"
                return {
                    'track_name': track_name,
                    'artist_name': artist_name,
                    'track_duration_ms': track_duration_ms,
                    'track_duration_m_and_s': f"{int(minutes)}:{int(seconds):02d}",
                    'album_cover_url': album_cover_url,
                    'guitar_tuning': guitar_tuning,
                    'guitar_capo': guitar_capo,
                    'main_chords_body': main_chords_body,
                    'complete_source_code_link': complete_source_code_link,
                    'complete_source_code_found': complete_source_code_found,
                    'musixmatch_lyrics_is_linesynced': musixmatch_lyrics_is_linesynced,
                    'found_musixmatch_lyrics': found_musixmatch_lyrics,
                    'spotify_error': spotify_error,
                    'track_bpm': track_bpm,
                    'sync_ratio_percentage': sync_ratio_percentage,
                    'track_key': track_key
                }
                
        # No chords found, also regard as no synced lyrics found    
        else:
            synced_lyrics_json, found_musixmatch_lyrics, musixmatch_lyrics_is_linesynced = getSyncedLyricsJson(track_id, artist_name, track_name)
            
            if (dev_or_prod == "DEVELOPMENT" and log_on_off == "ON" and wrote_block_3 != track_id):
                with open(log_file_path, 'a') as file:
                    wrote_block_3 = track_id
                    
                    file.write(f"FOUND LYRICS: {'YES' if found_musixmatch_lyrics else 'NO'}\n")
                    file.write(f"LYRICS ARE LINE SYNCED: {'YES' if musixmatch_lyrics_is_linesynced else 'NO'}\n")
                    file.write(f"-----\n")
                    
            ####################################
                    
            guitar_tuning = "E A D G B E"
            guitar_capo = "0"
            
            spotify_error = 1
                        
            found_musixmatch_lyrics = 0
            musixmatch_lyrics_is_linesynced = 0
            
            sync_ratio_percentage = "0%"
            
            return {
                'track_name': track_name,
                'artist_name': artist_name,
                'track_duration_ms': track_duration_ms,
                'track_duration_m_and_s': f"{int(minutes)}:{int(seconds):02d}",
                'album_cover_url': album_cover_url,
                'guitar_tuning': guitar_tuning,
                'guitar_capo': guitar_capo,
                'main_chords_body': main_chords_body,
                'complete_source_code_link': complete_source_code_link,
                'complete_source_code_found': complete_source_code_found,
                'musixmatch_lyrics_is_linesynced': musixmatch_lyrics_is_linesynced,
                'found_musixmatch_lyrics': found_musixmatch_lyrics,
                'spotify_error': spotify_error,
                'track_bpm': track_bpm,
                'sync_ratio_percentage': sync_ratio_percentage,
                'track_key': track_key
            }
    
    # Can't request Spotify (user might need to start Spotify and select song first)
    else:
        complete_source_code_link = ""
        complete_source_code_found = 0
        
        guitar_tuning = "E A D G B E"
        guitar_capo = "0"
                
        main_chords_body  = "Open Spotify somewhere and select a song."
        
        found_musixmatch_lyrics = 0
        musixmatch_lyrics_is_linesynced = 0
        
        track_bpm = 0
        track_key = 0
        
        sync_ratio_percentage = "0%"
        
        spotify_error = 1
        
        return {
            'track_name': "Track",
            'artist_name': "Artist",
            'track_duration_ms': "",
            'track_duration_m_and_s': "0:00",
            'album_cover_url': "",
            'guitar_tuning': guitar_tuning,
            'guitar_capo': guitar_capo,
            'main_chords_body': main_chords_body,
            'complete_source_code_link': "javascript:void(0)",
            'complete_source_code_found': complete_source_code_found,
            'musixmatch_lyrics_is_linesynced': musixmatch_lyrics_is_linesynced,
            'found_musixmatch_lyrics': found_musixmatch_lyrics,
            'spotify_error': spotify_error,
            'track_bpm': track_bpm,
            'sync_ratio_percentage': sync_ratio_percentage,
            'track_key': track_key
        }


######## ULTIMATE GUITAR SCRAPING ########
# Returns the source code, the link to the source, and 0 or 1 if the source code was found or not
def googleChordsForDB(track_name, artist_name, track_id):
    db = get_database(DATABASE_UE)
    cursor = db.cursor()
    cursor.execute('SELECT artist_name, track_name, save_timestamp, complete_source_code, complete_source_code_link, complete_source_code_found, result_index FROM ue_db WHERE track_id = ?', (track_id,))
    cached_data = cursor.fetchone()
    
    if cached_data:
        artist_name = cached_data[0]
        track_name = cached_data[1]
        save_timestamp_str = cached_data[2]
        save_timestamp = datetime.datetime.strptime(save_timestamp_str, '%Y-%m-%d %H:%M:%S.%f')
        complete_source_code = cached_data[3]
        complete_source_code_link = cached_data[4]
        complete_source_code_found = cached_data[5]
        result_index = cached_data[6]
        print(f'Found ue in database')
        
        # renew ue in database if older than X days
        days_to_renew = 30
        current_date = datetime.datetime.now()
        if (current_date - save_timestamp).days > days_to_renew:
            try:
                complete_source_code, complete_source_code_link, complete_source_code_found, result_index = googleChords(track_name, artist_name)
                if (complete_source_code_found == 0):
                    cursor.close()
                    return complete_source_code, complete_source_code_link, complete_source_code_found, result_index
                cursor.execute('INSERT OR REPLACE INTO ue_db (track_id, artist_name, track_name, save_timestamp, complete_source_code, complete_source_code_link, complete_source_code_found, result_index) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (track_id, artist_name, track_name, datetime.datetime.now(), complete_source_code, complete_source_code_link, complete_source_code_found, result_index))
                db.commit()
                print(f'UE found in database but outdated, now in ue database')
                cursor.close()
                return complete_source_code, complete_source_code_link, complete_source_code_found, result_index
            except Exception as e:
                ic(f'Requested ue to renew in database, as it is older than {days_to_renew} days, failed, used old one: {e}')
                artist_name = cached_data[0]
                track_name = cached_data[1]
                save_timestamp = cached_data[2]
                complete_source_code = json.loads(cached_data[3])
                complete_source_code_link = cached_data[4]
                complete_source_code_found = cached_data[5]
                result_index = cached_data[6]
                cursor.close()
                return complete_source_code, complete_source_code_link, complete_source_code_found, result_index
        else:
            cursor.close()
            return complete_source_code, complete_source_code_link, complete_source_code_found, result_index
    
    else:
        complete_source_code, complete_source_code_link, complete_source_code_found, result_index = googleChords(track_name, artist_name)
        # do not save if no source code found
        if (complete_source_code_found == 0):
            cursor.close()
            return complete_source_code, complete_source_code_link, complete_source_code_found, result_index
        cursor.execute('INSERT OR REPLACE INTO ue_db (track_id, artist_name, track_name, save_timestamp, complete_source_code, complete_source_code_link, complete_source_code_found, result_index) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (track_id, artist_name, track_name, datetime.datetime.now(), complete_source_code, complete_source_code_link, complete_source_code_found, result_index))
        db.commit()
        print(f'ue not found in database, but now in ue database')
        cursor.close()
        return complete_source_code, complete_source_code_link, complete_source_code_found, result_index
    
    cursor.close()
            
                
def googleChords(track_name, artist_name): 
    global spotify_error
    print("googled for chords, and used API")
    ### Example Response to prevent daily free Google API quota from being exceeded
    """
    url = 'https://tabs.ultimate-guitar.com/tab/dekker/maybe-october-chords-4033981'
    try:
        response = requests.get(url)
        if response.status_code == 200:
            html_content = response.text
            return html_content, url, 1
        else:
            return "EXAMPLE SOURCE CODE FAILED", url, 0
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    """
    ###
    
    # remove keywords for remastered version songs as they might hinder the search
    query = f'{artist_name} {track_name.lower().replace("remastered", "").replace("remaster", "").replace("version", "")} chords Ultimate Guitar'
    
    search_url = f"https://www.googleapis.com/customsearch/v1?key={google_api_key}&cx={google_search_engine_id}&q={query}"
    
    desired_url_substring = 'tabs.ultimate-guitar.com/tab'
    
    result_index = 0

    try:
        #raise Exception("To not succeed daily free Google API quota -> Raise Exception to respond with example source code")
        response = requests.get(search_url)
        response.raise_for_status()
        search_results = response.json()
                
        if 'items' in search_results and len(search_results['items']) > 0:
            
            # Iterate over the (first ten) search results 
            for result in search_results['items'][:10]:
                result_index += 1
                
                link = result.get('link', '')
                #ic('POSSIBLE LINK: ' + link)
                
                # Check if the link contains the desired substring (i.e. is on Ultimate Guitar)
                if desired_url_substring in link:
                    #ic('FOUND THIS LINK: ' + link)

                    page_response = requests.get(link)
                    page_response.raise_for_status()
                    source_code = page_response.text
                    
                    source_code_soup = BeautifulSoup(source_code, 'html.parser')
                    title_tag = source_code_soup.find('title')
                    title_text = title_tag.text
                    
                    # Check if the found Ultimate Guitar link depicts the desired song
                    # The title on Ultimate Guitar may look something like this: <title>BREATHE CHORDS (ver 2) by Pink Floyd @ Ultimate-Guitar.Com</title>
                    # Or like this: ONE CHORDS by Metallica for guitar, ukulele, piano at Ultimate-Guitar
                    title_text_no_ver = (re.sub(r'\(ver \d+\)', '', title_text)).replace("  ", " ") # e.g BREATHE CHORDS by Pink Floyd @ Ultimate-Guitar.Com
                    title_text_no_ug = title_text_no_ver.replace(" @ Ultimate-Guitar.Com", "") # e.g BREATHE CHORDS by Pink Floyd 
                    title_text_no_ug = title_text_no_ug.replace(" for guitar, ukulele, piano at Ultimate-Guitar", "") # e.g BREATHE CHORDS by Pink Floyd
                    title_text_no_ug = title_text_no_ug.lower() # e.g. breathe chords by pink floyd
                    
                    # if "chords" exists in title
                    if (title_text_no_ug.find("chords") != -1):
                        
                        ug_track_name = title_text_no_ug.split("chords by")[0].strip() # e.g. breathe
                        ug_artist_name = title_text_no_ug.split("chords by")[1].strip() # e.g. pink floyd
                        ic(ug_track_name)
                        ic(ug_artist_name)
                        
                        spotify_track_name = (track_name.lower().replace('remastered', '').replace('remaster', '').replace('version', '')).strip() # e.g. Breathe - 2011 Remastered Version -> breathe - 2011
                        spotify_track_name = re.sub(r'\s- \s\d{4}', '', spotify_track_name) # both replace year
                        spotify_track_name = re.sub(r'\s-\s\d{4}', '', spotify_track_name)

                        spotify_artist_name = artist_name.lower().strip() # e.g. Pink Floyd
                        ic(spotify_track_name)
                        ic(spotify_artist_name)
                        
                        #ic(fuzz.ratio(ug_track_name, spotify_track_name))
                        #ic(fuzz.ratio(ug_artist_name, spotify_artist_name))
                        
                        # Often titles on spotify include further things like (acoustic, version, remastered, unplugged), title are often the exact same, thus different ratio thresholds
                        if (fuzz.ratio(ug_track_name, spotify_track_name) >= 40) and (fuzz.ratio(ug_artist_name, spotify_artist_name) >= 40):
                            return source_code, link, 1, result_index
    
                
            ic("COULDN'T FIND ANY CHORDS FOR THAT SONG")
            return "Couldn't find chords for that song.", "https://www.google.de/search?q=" + query, 0, 0
        
        else:
            ic("GOOGLE SEARCH FOR CHORDS FAILED")
            return "Google for chords failed.", "https://www.google.de/search?q=" + query, 0, 0
        
    except Exception as e:
        ic("Probably exceeded daily free Google API quota")
        ic(f"Error: {e}")
        return "Google for chords failed - daily quota exceeded.", "https://www.google.de/search?q=" + query, 0, 0
        #return example_source()

# Returns the tuning values of the guitar, e.g. "E A D G B E"
def extractTuning(complete_source_code):
    pattern = r'tuning&quot;:{&quot;name&quot;:&quot;([^&]+)&quot;,&quot;value&quot;:&quot;([^&]+)&quot;'
    match = re.search(pattern, complete_source_code)
    
    if match:
        # name e.g. 'Standard'
        name = match.group(1)
        # value e.g. 'E A D G B E'
        value = match.group(2)
        return value
    else:
        # If no tuning was provided, return the standard tuning
        return "E A D G B E"

# Returns the capo value of the guitar, e.g. "0"
def extractCapo(complete_source_code):
    pattern = r'{&quot;capo&quot;:([^&]+),&quot'
    match = re.search(pattern, complete_source_code)
    
    if match:
        return re.sub(r'[^0-9]', '', match.group(1))
    else:
        # If no capo was provided, return 0 for no capo
        return "0"

# Returns the main chords/lyrics content of the source code (modified with <br> and <span> tags for chords)
def extractMainChordsBody(complete_source_code, align):
    start_string = "{&quot;content&quot;:&quot;"
    end_string = "&quot;,&quot;revision_id&quot;"

    pattern = re.compile(re.escape(start_string) + r'(.*?)' + re.escape(end_string))
    match = pattern.search(complete_source_code)
    
    if match:
        result = match.group(1)
        if align != "middle":
            # Modify source code to include line breaks and span tags for chords (don't do if client requests middle align)
            result = replace_spaces_within_chords(result)
        return result.replace("\\r\\n", "<br>").replace("[ch]", '<span class="chord_span">').replace("[/ch]", "</span>").replace("[tab]", "").replace("[/tab]", "").replace('\&quot;', '"')
    else:
        return "Failed to find main chords/lyrics content of the source code"

def replace_spaces_within_chords(input_string):
    pattern = re.compile(r'\[tab\](\s+)\[ch\]')
    pattern_2 = re.compile(r'\[/ch\](\s+)\[ch\]')

    def replace_1(match):
        spaces = match.group(1)
        nbsp_replacement = '&nbsp;' * len(spaces)
        return f'[tab]{nbsp_replacement}[ch]'
    
    def replace_2(match):
        spaces = match.group(1)
        nbsp_replacement = '&nbsp;' * len(spaces)
        return f'[/ch]{nbsp_replacement}[ch]'

    result_string_1 = re.sub(pattern, replace_1, input_string)
    result_string_2 = re.sub(pattern_2, replace_2, result_string_1)

    return result_string_2


######## MUSIXMATCH API ########
# Returns the synced lyrics json from the musixmatch (respectively free GitHub) API
def getSyncedLyricsJson(track_id, artist_name, track_name):
    global found_musixmatch_lyrics
    global musixmatch_lyrics_is_linesynced
    
    
    ### REST API APPROACH:
    # MusixMatchs' free API doesn't include synced lyrics (i.e. timestamps) as well as just a part of the lyrics 
    # Akashrchandran (GitHub) provides a free API endpoint for the full synced lyrics
    # https://github.com/akashrchandran/spotify-lyrics-api
    if (lyrics_api_source == "REST"):
        url = "https://spotify-lyric-api-984e7b4face0.herokuapp.com/?trackid=" + str(track_id)    
        
        try:
            response = requests.get(url)
            response.raise_for_status() 
            origin_string = response.text
            response_json = json.loads(origin_string)
            # ic(response_json)
            
            # Found lyrics but not synced
            if 'syncType' in response_json and response_json['syncType'] == 'UNSYNCED':
                found_musixmatch_lyrics = 1
                musixmatch_lyrics_is_linesynced = 0
                return "JUST FOUND UNSYNCED LYRICS", found_musixmatch_lyrics, musixmatch_lyrics_is_linesynced
            
            # Found synced lyrics
            elif 'syncType' in response_json and response_json['syncType'] == 'LINE_SYNCED':
                found_musixmatch_lyrics = 1
                musixmatch_lyrics_is_linesynced = 1
                return response_json, found_musixmatch_lyrics, musixmatch_lyrics_is_linesynced
            
            # Probably found lyrics but with other error (regard as not found)
            else:
                found_musixmatch_lyrics = 0
                musixmatch_lyrics_is_linesynced = 0
                return "FOUND LYRICS, ERROR IN RESPONSE", found_musixmatch_lyrics, musixmatch_lyrics_is_linesynced

        # Couldn't find lyrics
        except Exception as e:
            found_musixmatch_lyrics = 0
            musixmatch_lyrics_is_linesynced = 0
            ic(f'Error making lyrics request, Perhaps no lyrics available: {e}')
            return "COULDN'T FIND LYRICS, ERROR REQUESTING", found_musixmatch_lyrics, musixmatch_lyrics_is_linesynced
    
    
    ### SELF-MADE SPOTIFY LYRICS APPROACH:
    if (lyrics_api_source == "LRCLIB"):
        # Make this song appear like it has no lyrics, for study: 1vxw6aYJls2oq3gW0DujAo
        if (track_id == "ignoreThisIf"):
            found_musixmatch_lyrics = 0
            musixmatch_lyrics_is_linesynced = 0
            #ic(f'Crazy by Gnarls Barkley has no synced lyrics') 
            return "COULDN'T FIND LYRICS, ERROR REQUESTING", found_musixmatch_lyrics, musixmatch_lyrics_is_linesynced
        
        db = get_database(DATABASE_LYRICS)
        cursor = db.cursor()
        cursor.execute('SELECT artist_name, track_name, save_timestamp, original_json FROM lyrics_db WHERE track_id = ?', (track_id,))
        cached_data = cursor.fetchone()
        
        if cached_data:
            artist_name = cached_data[0]
            track_name = cached_data[1]
            save_timestamp_str = cached_data[2]
            save_timestamp = datetime.datetime.strptime(save_timestamp_str, '%Y-%m-%d %H:%M:%S.%f')
            original_json = json.loads(cached_data[3])
            print(f'Found lyrics in database')
            
            # renew lyrics in database if older than X days
            days_to_renew = 30
            current_date = datetime.datetime.now()
            if (current_date - save_timestamp).days > days_to_renew:
                try:
                    original_json = getLyrics.get_lyrics(track_id, artist_name, track_name)
                    cursor.execute('INSERT OR REPLACE INTO lyrics_db (track_id, artist_name, track_name, save_timestamp, original_json) VALUES (?, ?, ?, ?, ?)', (track_id, artist_name, track_name, datetime.datetime.now(), json.dumps(original_json)))
                    db.commit()
                    print(f'Lyrics found in database but outdated, now in lyrics_db')
                except Exception as e:
                    ic(f'Requested lyrics to renew in database, as it is older than {days_to_renew} days, failed, used old one: {e}')
                    artist_name = cached_data[0]
                    track_name = cached_data[1]
                    save_timestamp = cached_data[2]
                    original_json = json.loads(cached_data[3])
        else:
            try:
                original_json = getLyrics.get_lyrics(track_id, artist_name, track_name)
                cursor.execute('INSERT OR REPLACE INTO lyrics_db (track_id, artist_name, track_name, save_timestamp, original_json) VALUES (?, ?, ?, ?, ?)', (track_id, artist_name, track_name, datetime.datetime.now(), json.dumps(original_json)))
                db.commit()
                print(f'Lyrics not found in database, but now in lyrics_db')
            except Exception as e:
                found_musixmatch_lyrics = 0
                musixmatch_lyrics_is_linesynced = 0
                ic(f'Error making lyrics request, Perhaps no lyrics available: {e}')
                return "COULDN'T FIND LYRICS, ERROR REQUESTING", found_musixmatch_lyrics, musixmatch_lyrics_is_linesynced
        
        cursor.close()
            
        try:
            #original_json = getLyrics.getLyrics(track_id)
            response_json = {'lines': original_json['lyrics']['lines'], "syncType":  original_json['lyrics']['syncType']}
            # ic(original_json)
            
            # Found lyrics but not synced
            if 'syncType' in response_json and response_json['syncType'] == 'UNSYNCED':
                found_musixmatch_lyrics = 1
                musixmatch_lyrics_is_linesynced = 0
                return "JUST FOUND UNSYNCED LYRICS", found_musixmatch_lyrics, musixmatch_lyrics_is_linesynced
            
            # Found synced lyrics
            elif 'syncType' in response_json and response_json['syncType'] == 'LINE_SYNCED':
                found_musixmatch_lyrics = 1
                musixmatch_lyrics_is_linesynced = 1
                return response_json, found_musixmatch_lyrics, musixmatch_lyrics_is_linesynced
            
            # Probably found lyrics but with other error (regard as not found)
            else:
                found_musixmatch_lyrics = 0
                musixmatch_lyrics_is_linesynced = 0
                return "FOUND LYRICS, ERROR IN RESPONSE", found_musixmatch_lyrics, musixmatch_lyrics_is_linesynced

        # Couldn't find lyrics
        except Exception as e:
            found_musixmatch_lyrics = 0
            musixmatch_lyrics_is_linesynced = 0
            ic(f'Error making lyrics request, Perhaps no lyrics available: {e}')
            return "COULDN'T FIND LYRICS, ERROR REQUESTING", found_musixmatch_lyrics, musixmatch_lyrics_is_linesynced
    
# Returns an array of tupels of the form (timestamp, lyrics line) (e.g. [(19100, 'Up with the worry and down in a flurry'), ...])
def parseSyncedLyricsJsonToTupelArray(synced_lyrics_json):
    global musixmatch_lyrics_is_linesynced
    
    if musixmatch_lyrics_is_linesynced == 0:
        return []
    
    lines = synced_lyrics_json.get('lines', [])
    tupelArray = [(int(line['startTimeMs']), line['words']) for line in lines]
    return tupelArray


######## TIMESTAMP -> SOURCE CODE INSERTION ########
# Main algorithm that inserts Musixmatch timestamps into the Ultimate Guitar source code
def insertTimestampsToMainChordsBody(synced_lyrics_tupel_array, main_chords_body, track_length_ms, track_id):  
    global wrote_block_4
    global sync_ratio_percentage
    
    # Removes all empty lyrics and music notes from Musixmatch lyrics, as they can't be matched anyways and cause errors in red and blue paths
    synced_lyrics_tupel_array = [(timestamp, lyric) for timestamp, lyric in synced_lyrics_tupel_array if lyric not in ['', '♪']]
    #ic(synced_lyrics_tupel_array)
    
    # Array of all new lines in the source code  
    main_chords_body_line_array = main_chords_body.split("<br>")
    
    # Array of occurences of "only" real lyrics line from Ultimate Guitar with index where it occurs (unescape html to make e.g. Steht&#039;s -> Steht's)
    main_chords_body_line_array_lyrics_with_index = [
        [index, html.unescape(line)] for index, line in enumerate(main_chords_body_line_array)
        if not (line == "" or "chord_span" in line or "[" in line or "]" in line or "|-" in line or "-|" in line or "capo" in line.lower() or "n.c." in line.lower() or "tuning" in line.lower())
    ]
    
    # Add "NOTSYNCED" to each line which will then be replaced with the timestamp
    main_chords_body_line_array_lyrics_with_index_and_timestamp = [["NOTSYNCED", t[0], html.unescape(t[1])] for t in main_chords_body_line_array_lyrics_with_index]
    
    # Inserts timestamps into main_chords_body_line_array_lyrics_with_index_and_timestamp by fuzzy lyrics matching
    # official_lyrics_line = Lyrics Line from MusixMatch API
    # unofficial_lyrics_line = Lyrics Line from Ultimate Guitar
    amm_of_lines_succ_synced = 0
    insert_hit = 0         
    official_lyrics_line = 0
    max_unoffical_line_iteration = 0
    # Defines that maximum ammount of next lines to check on UG when trying to match MusixMatch (mean and 1/6 of it, and round up) (was about 5 hardcoded before)
    unofficial_line_iteration_check_range = math.ceil(((len(main_chords_body_line_array_lyrics_with_index) + len(synced_lyrics_tupel_array)) / 2) / 6)
    
    amm_of_lines_to_sync = len(synced_lyrics_tupel_array)
    green_path_ratio_COUNTER = 0
    red_path_ratio_COUNTER = 0
    red_path_ratio_3_COUNTER = 0
    red_path_ratio_4_COUNTER = 0
    blue_path_ratio_COUNTER = 0
    blue_path_ratio_3_COUNTER = 0
    blue_path_ratio_4_COUNTER = 0
    
    
    # Iterate through all Musixmatch lyrics lines
    while official_lyrics_line < len(synced_lyrics_tupel_array):
        
        # Only alway search - for every official lyrics line - the next five unofficial lyrics lines
        # Only if first match was found (insert_hit != 0) check next three unofficial lyrics lines
        # Thus not regard any informative text in the source code before the first unofficial lyrics lines occurs
        if (insert_hit == 0):
            max_unoffical_line_iteration = len(main_chords_body_line_array_lyrics_with_index)
        else:
            max_unoffical_line_iteration = insert_hit + unofficial_line_iteration_check_range
            if max_unoffical_line_iteration >= len(main_chords_body_line_array_lyrics_with_index):
                max_unoffical_line_iteration = len(main_chords_body_line_array_lyrics_with_index)
                
        for unofficial_lyrics_line in range (insert_hit, max_unoffical_line_iteration):
            
            green_path_ratio = 0
            red_path_ratio = 0
            red_path_ratio_3 = 0
            red_path_ratio_4 = 0
            blue_path_ratio = 0
            blue_path_ratio_3 = 0
            blue_path_ratio_4 = 0
            
            
            ### Get fuzzy ratios for all possible paths ###
            
            # Official lyrics fuzzy matches unofficial lyrics (GREEN)
            fuzzy_lyrics_line_ratio = fuzz.ratio(synced_lyrics_tupel_array[official_lyrics_line][1].lower(), main_chords_body_line_array_lyrics_with_index[unofficial_lyrics_line][1].lower())
            if fuzzy_lyrics_line_ratio >= 70:
                green_path_ratio = fuzzy_lyrics_line_ratio
                
            # One official lyrics line fuzzy matches two consecutive unofficial lyrics lines (RED)
            if unofficial_lyrics_line < len(main_chords_body_line_array_lyrics_with_index)-1:
                fuzzy_onelineofficial_is_twolineunofficial = fuzz.ratio(synced_lyrics_tupel_array[official_lyrics_line][1].lower(), main_chords_body_line_array_lyrics_with_index[unofficial_lyrics_line][1].lower() + " " + main_chords_body_line_array_lyrics_with_index[unofficial_lyrics_line+1][1].lower())
                if fuzzy_onelineofficial_is_twolineunofficial >= 70: 
                    # https://prnt.sc/r0ZLk4Dv3aBP (Check Green Path of current OFF line with next UNOFF line)
                    # Skip if that Green Path is desired (Prevent Screenshot Red Lines) (Or Check Another Love by Tom Odell)
                    green_path_ratio_next = fuzz.ratio(synced_lyrics_tupel_array[official_lyrics_line][1].lower(), main_chords_body_line_array_lyrics_with_index[unofficial_lyrics_line+1][1].lower())
                    if (green_path_ratio_next >= fuzzy_onelineofficial_is_twolineunofficial):
                        continue
                    red_path_ratio = fuzzy_onelineofficial_is_twolineunofficial
                    
            # One official lyrics line fuzzy matches three consecutive unofficial lyrics lines (RED 3)
            if unofficial_lyrics_line < len(main_chords_body_line_array_lyrics_with_index)-2:
                fuzzy_onelineofficial_is_threelineunofficial = fuzz.ratio(synced_lyrics_tupel_array[official_lyrics_line][1].lower(), main_chords_body_line_array_lyrics_with_index[unofficial_lyrics_line][1].lower() + " " + main_chords_body_line_array_lyrics_with_index[unofficial_lyrics_line+1][1].lower() + " " + main_chords_body_line_array_lyrics_with_index[unofficial_lyrics_line+2][1].lower())
                if fuzzy_onelineofficial_is_threelineunofficial >= 70:
                    
                    green_path_ratio_next_next = fuzz.ratio(synced_lyrics_tupel_array[official_lyrics_line][1].lower(), main_chords_body_line_array_lyrics_with_index[unofficial_lyrics_line+2][1].lower())
                    fuzzy_onelineofficial_is_twolineunofficial_next = fuzz.ratio(synced_lyrics_tupel_array[official_lyrics_line][1].lower(), main_chords_body_line_array_lyrics_with_index[unofficial_lyrics_line+1][1].lower() + " " + main_chords_body_line_array_lyrics_with_index[unofficial_lyrics_line+2][1].lower())

                    if (green_path_ratio_next_next >= fuzzy_onelineofficial_is_threelineunofficial):
                        continue
                    if (fuzzy_onelineofficial_is_twolineunofficial_next >= fuzzy_onelineofficial_is_threelineunofficial):
                        continue
                    
                    red_path_ratio_3 = fuzzy_onelineofficial_is_threelineunofficial
            
            # One official lyrics line fuzzy matches four consecutive unofficial lyrics lines (RED 4)
            if unofficial_lyrics_line < len(main_chords_body_line_array_lyrics_with_index)-3:
                fuzzy_onelineofficial_is_fourlineunofficial = fuzz.ratio(synced_lyrics_tupel_array[official_lyrics_line][1].lower(), main_chords_body_line_array_lyrics_with_index[unofficial_lyrics_line][1].lower() + " " + main_chords_body_line_array_lyrics_with_index[unofficial_lyrics_line+1][1].lower() + " " + main_chords_body_line_array_lyrics_with_index[unofficial_lyrics_line+2][1].lower() + " " + main_chords_body_line_array_lyrics_with_index[unofficial_lyrics_line+3][1].lower())
                if fuzzy_onelineofficial_is_fourlineunofficial >= 70:
                    
                    green_path_ratio_next_next_next = fuzz.ratio(synced_lyrics_tupel_array[official_lyrics_line][1].lower(), main_chords_body_line_array_lyrics_with_index[unofficial_lyrics_line+3][1].lower())
                    fuzzy_onelineofficial_is_threelineunofficial_next = fuzz.ratio(synced_lyrics_tupel_array[official_lyrics_line][1].lower(), main_chords_body_line_array_lyrics_with_index[unofficial_lyrics_line+1][1].lower() + " " + main_chords_body_line_array_lyrics_with_index[unofficial_lyrics_line+2][1].lower() + " " + main_chords_body_line_array_lyrics_with_index[unofficial_lyrics_line+3][1].lower())

                    if (green_path_ratio_next_next_next >= fuzzy_onelineofficial_is_fourlineunofficial):
                        continue
                    if (fuzzy_onelineofficial_is_threelineunofficial_next >= fuzzy_onelineofficial_is_fourlineunofficial):
                        continue
                    
                    red_path_ratio_4 = fuzzy_onelineofficial_is_fourlineunofficial
                    
            # Two consecutive official lyric lines fuzzy matches one unofficial lyric line (BLUE)
            if official_lyrics_line < len(synced_lyrics_tupel_array)-1:
                fuzzy_twolineofficial_is_onelineunofficial = fuzz.ratio(synced_lyrics_tupel_array[official_lyrics_line][1].lower() + " " + synced_lyrics_tupel_array[official_lyrics_line+1][1].lower(), main_chords_body_line_array_lyrics_with_index[unofficial_lyrics_line][1].lower())
                if fuzzy_twolineofficial_is_onelineunofficial >= 70:
                    
                    green_path_ratio_next = fuzz.ratio(synced_lyrics_tupel_array[official_lyrics_line+1][1].lower(), main_chords_body_line_array_lyrics_with_index[unofficial_lyrics_line][1].lower())
                    if (green_path_ratio_next >= fuzzy_twolineofficial_is_onelineunofficial):
                        continue
                    
                    blue_path_ratio = fuzzy_twolineofficial_is_onelineunofficial
                    
            # Three consecutive official lyric lines fuzzy matches one unofficial lyric line (BLUE 3)
            if official_lyrics_line < len(synced_lyrics_tupel_array)-2:
                fuzzy_threelineofficial_is_onelineunofficial = fuzz.ratio(synced_lyrics_tupel_array[official_lyrics_line][1].lower() + " " + synced_lyrics_tupel_array[official_lyrics_line+1][1].lower() + " " + synced_lyrics_tupel_array[official_lyrics_line+2][1].lower(), main_chords_body_line_array_lyrics_with_index[unofficial_lyrics_line][1].lower())
                if fuzzy_threelineofficial_is_onelineunofficial >= 70:
                    
                    green_path_ratio_next_next = fuzz.ratio(synced_lyrics_tupel_array[official_lyrics_line+2][1].lower(), main_chords_body_line_array_lyrics_with_index[unofficial_lyrics_line][1].lower())
                    if (green_path_ratio_next_next >= fuzzy_threelineofficial_is_onelineunofficial):
                        continue
                    
                    blue_path_ratio_3 = fuzzy_threelineofficial_is_onelineunofficial
                    
            # Four consecutive official lyric lines fuzzy matches one unofficial lyric line (BLUE 4)
            if official_lyrics_line < len(synced_lyrics_tupel_array)-3:
                fuzzy_fourlineofficial_is_onelineunofficial = fuzz.ratio(synced_lyrics_tupel_array[official_lyrics_line][1].lower() + " " + synced_lyrics_tupel_array[official_lyrics_line+1][1].lower() + " " + synced_lyrics_tupel_array[official_lyrics_line+2][1].lower() + " " + synced_lyrics_tupel_array[official_lyrics_line+3][1].lower(), main_chords_body_line_array_lyrics_with_index[unofficial_lyrics_line][1].lower())
                if fuzzy_fourlineofficial_is_onelineunofficial >= 70:
                    
                    green_path_ratio_next_next_next = fuzz.ratio(synced_lyrics_tupel_array[official_lyrics_line+3][1].lower(), main_chords_body_line_array_lyrics_with_index[unofficial_lyrics_line][1].lower())
                    if (green_path_ratio_next_next_next >= fuzzy_fourlineofficial_is_onelineunofficial):
                        continue
                    
                    blue_path_ratio_4 = fuzzy_fourlineofficial_is_onelineunofficial
                    
            
            ### Decide which path to take ### #########################################################
                    
            # GREEN PATH
            if green_path_ratio > red_path_ratio and green_path_ratio > blue_path_ratio and green_path_ratio > blue_path_ratio_3 and green_path_ratio > red_path_ratio_3 and green_path_ratio > red_path_ratio_4 and green_path_ratio > blue_path_ratio_4:
                main_chords_body_line_array_lyrics_with_index_and_timestamp[unofficial_lyrics_line][0] = str(synced_lyrics_tupel_array[official_lyrics_line][0]) + "\" class='ONE_LINE_OFF_IS_ONE_UNOFF'"
                amm_of_lines_succ_synced += 1
                insert_hit = unofficial_lyrics_line + 1
                green_path_ratio_COUNTER += 1
                break
            
            # RED PATH
            elif red_path_ratio > green_path_ratio and red_path_ratio > blue_path_ratio and red_path_ratio > blue_path_ratio_3 and red_path_ratio > red_path_ratio_3 and red_path_ratio > red_path_ratio_4 and red_path_ratio > blue_path_ratio_4:
                # Mean of two timestamps and its delta plus
                try:
                    timestamp_for_second_line = ((synced_lyrics_tupel_array[official_lyrics_line][0] + synced_lyrics_tupel_array[official_lyrics_line + 1][0]) / 2) - synced_lyrics_tupel_array[official_lyrics_line][0]
                except:
                    timestamp_for_second_line = 1500
                
                main_chords_body_line_array_lyrics_with_index_and_timestamp[unofficial_lyrics_line][0] = str(synced_lyrics_tupel_array[official_lyrics_line][0]) + "\" class='ONE_LINE_OFF_IS_MORE_UNOFF'"
                main_chords_body_line_array_lyrics_with_index_and_timestamp[unofficial_lyrics_line+1][0] = str(synced_lyrics_tupel_array[official_lyrics_line][0] + timestamp_for_second_line) + "\" class='ONE_LINE_OFF_IS_MORE_UNOFF'"
                
                amm_of_lines_succ_synced += 1
                insert_hit = unofficial_lyrics_line + 2
                red_path_ratio_COUNTER += 1
                break
            
            # RED PATH 3
            elif red_path_ratio_3 > green_path_ratio and red_path_ratio_3 > blue_path_ratio and red_path_ratio_3 > blue_path_ratio_3 and red_path_ratio_3 > red_path_ratio and red_path_ratio_3 > red_path_ratio_4 and red_path_ratio_3 > blue_path_ratio_4:
                # Disperse timstamps by 1/3 and 2/3 of the delta
                try:
                    timestamp_for_second_line = ((synced_lyrics_tupel_array[official_lyrics_line][0] + (1/3) * (synced_lyrics_tupel_array[official_lyrics_line + 1][0] - synced_lyrics_tupel_array[official_lyrics_line][0]))) - synced_lyrics_tupel_array[official_lyrics_line][0]
                    timestamp_for_third_line =  ((synced_lyrics_tupel_array[official_lyrics_line][0] + (2/3) * (synced_lyrics_tupel_array[official_lyrics_line + 1][0] - synced_lyrics_tupel_array[official_lyrics_line][0]))) - synced_lyrics_tupel_array[official_lyrics_line][0]
                except:
                    timestamp_for_second_line = 1500
                    timestamp_for_third_line = 3000
                
                main_chords_body_line_array_lyrics_with_index_and_timestamp[unofficial_lyrics_line][0] = str(synced_lyrics_tupel_array[official_lyrics_line][0]) + "\" class='MORE_LINE_OFF_IS_ONE_UNOFF'"
                main_chords_body_line_array_lyrics_with_index_and_timestamp[unofficial_lyrics_line+1][0] = str(synced_lyrics_tupel_array[official_lyrics_line][0] + timestamp_for_second_line) + "\" class='MORE_LINE_OFF_IS_ONE_UNOFF'"
                main_chords_body_line_array_lyrics_with_index_and_timestamp[unofficial_lyrics_line+2][0] = str(synced_lyrics_tupel_array[official_lyrics_line][0] + timestamp_for_third_line) + "\" class='MORE_LINE_OFF_IS_ONE_UNOFF'"
                
                amm_of_lines_succ_synced += 1
                insert_hit = unofficial_lyrics_line + 3
                red_path_ratio_3_COUNTER += 1
                break
            
            # RED PATH 4
            elif red_path_ratio_4 > green_path_ratio and red_path_ratio_4 > blue_path_ratio and red_path_ratio_4 > blue_path_ratio_3 and red_path_ratio_4 > red_path_ratio and red_path_ratio_4 > red_path_ratio_3 and red_path_ratio_4 > blue_path_ratio_4:
                # Disperse timstamps by 1/4 and 2/4 and 3/4 of the delta
                try:
                    timestamp_for_second_line = ((synced_lyrics_tupel_array[official_lyrics_line][0] + (1/4) * (synced_lyrics_tupel_array[official_lyrics_line + 1][0] - synced_lyrics_tupel_array[official_lyrics_line][0]))) - synced_lyrics_tupel_array[official_lyrics_line][0]
                    timestamp_for_third_line =  ((synced_lyrics_tupel_array[official_lyrics_line][0] + (2/4) * (synced_lyrics_tupel_array[official_lyrics_line + 1][0] - synced_lyrics_tupel_array[official_lyrics_line][0]))) - synced_lyrics_tupel_array[official_lyrics_line][0]
                    timestamp_for_fourth_line = ((synced_lyrics_tupel_array[official_lyrics_line][0] + (3/4) * (synced_lyrics_tupel_array[official_lyrics_line + 1][0] - synced_lyrics_tupel_array[official_lyrics_line][0]))) - synced_lyrics_tupel_array[official_lyrics_line][0]
                except:
                    timestamp_for_second_line = 1500
                    timestamp_for_third_line = 3000
                    timestamp_for_fourth_line = 4500
                
                main_chords_body_line_array_lyrics_with_index_and_timestamp[unofficial_lyrics_line][0] = str(synced_lyrics_tupel_array[official_lyrics_line][0]) + "\" class='ONE_LINE_OFF_IS_MORE_UNOFF'"
                main_chords_body_line_array_lyrics_with_index_and_timestamp[unofficial_lyrics_line+1][0] = str(synced_lyrics_tupel_array[official_lyrics_line][0] + timestamp_for_second_line) + "\" class='ONE_LINE_OFF_IS_MORE_UNOFF'"
                main_chords_body_line_array_lyrics_with_index_and_timestamp[unofficial_lyrics_line+2][0] = str(synced_lyrics_tupel_array[official_lyrics_line][0] + timestamp_for_third_line) + "\" class='ONE_LINE_OFF_IS_MORE_UNOFF'"
                main_chords_body_line_array_lyrics_with_index_and_timestamp[unofficial_lyrics_line+3][0] = str(synced_lyrics_tupel_array[official_lyrics_line][0] + timestamp_for_fourth_line) + "\" class='ONE_LINE_OFF_IS_MORE_UNOFF'"
                
                amm_of_lines_succ_synced += 1
                insert_hit = unofficial_lyrics_line + 4
                red_path_ratio_4_COUNTER += 1
                break
            
            # BLUE PATH
            elif blue_path_ratio > green_path_ratio and blue_path_ratio > red_path_ratio and blue_path_ratio > blue_path_ratio_3 and blue_path_ratio > red_path_ratio_3 and blue_path_ratio > red_path_ratio_4 and blue_path_ratio > blue_path_ratio_4:
                main_chords_body_line_array_lyrics_with_index_and_timestamp[unofficial_lyrics_line][0] = str(synced_lyrics_tupel_array[official_lyrics_line][0]) + "\" class='MORE_LINE_OFF_IS_ONE_UNOFF'"
                amm_of_lines_succ_synced += 2
                insert_hit = unofficial_lyrics_line + 1
                # Skip next official lyrics line
                official_lyrics_line += 1
                blue_path_ratio_COUNTER += 1
                break  
            
            # BLUE PATH 3
            elif blue_path_ratio_3 > green_path_ratio and blue_path_ratio_3 > red_path_ratio and blue_path_ratio_3 > blue_path_ratio and blue_path_ratio_3 > red_path_ratio_3 and blue_path_ratio_3 > red_path_ratio_4 and blue_path_ratio_3 > blue_path_ratio_4:
                main_chords_body_line_array_lyrics_with_index_and_timestamp[unofficial_lyrics_line][0] = str(synced_lyrics_tupel_array[official_lyrics_line][0]) + "\" class='MORE_LINE_OFF_IS_ONE_UNOFF'"
                amm_of_lines_succ_synced += 3
                insert_hit = unofficial_lyrics_line + 1
                # Skip next two official lyrics lines
                official_lyrics_line += 2
                blue_path_ratio_3_COUNTER += 1
                break
            
            # BLUE PATH 4
            elif blue_path_ratio_4 > green_path_ratio and blue_path_ratio_4 > red_path_ratio and blue_path_ratio_4 > red_path_ratio_3 and blue_path_ratio_4 > red_path_ratio_4 and blue_path_ratio_4 > blue_path_ratio and blue_path_ratio_4 > blue_path_ratio_3:
                main_chords_body_line_array_lyrics_with_index_and_timestamp[unofficial_lyrics_line][0] = str(synced_lyrics_tupel_array[official_lyrics_line][0]) + "\" class='MORE_LINE_OFF_IS_ONE_UNOFF'"
                amm_of_lines_succ_synced += 4
                insert_hit = unofficial_lyrics_line + 1
                # Skip next two official lyrics lines
                official_lyrics_line += 3
                blue_path_ratio_4_COUNTER += 1
                break
             
        official_lyrics_line += 1  
       
    #print(f"AMMOUNT OF MUSIXMATCH LYRICS TO SYNC (without empty or note): {amm_of_lines_to_sync}\n")
    #print(f"AMMOUNT OF SUCCESSFULLY SYNCED MUSIXMATCH LYRICS: {amm_of_lines_succ_synced}\n")
    #print(f"SYNC RATIO: {(amm_of_lines_succ_synced/amm_of_lines_to_sync)*100}%\n")
    sync_ratio_percentage = round((amm_of_lines_succ_synced/amm_of_lines_to_sync)*100)
    print(f"SYNC RATIO: {sync_ratio_percentage}%")
    # If the Sync Ratio is below 60% return the original source code without any timestamps and regard as not synced
    if (sync_ratio_percentage < 60):
        return main_chords_body, True
                
    if (dev_or_prod == "DEVELOPMENT" and log_on_off == "ON" and wrote_block_4 != track_id):
            with open(log_file_path, 'a') as file:
                wrote_block_4 = track_id
                
                file.write(f"AMMOUNT OF MUSIXMATCH LYRICS TO SYNC (without empty or note): {amm_of_lines_to_sync}\n")
                file.write(f"AMMOUNT OF SUCCESSFULLY SYNCED MUSIXMATCH LYRICS: {amm_of_lines_succ_synced}\n")
                # file.write(f"AMMOUNT OF LYRICS (AND PERHAPS OTHER TEXT) LINES ON UG: {len(main_chords_body_line_array_lyrics_with_index_and_timestamp)}\n")
                file.write(f"SYNC RATIO: {(amm_of_lines_succ_synced/amm_of_lines_to_sync)*100}%\n")
                
                file.write(f"-----\n")
                
                file.write(f"GREEN PATH AMMOUNT: {green_path_ratio_COUNTER}\n")
                file.write(f"GREEN PATH PERCENTAGE: {(green_path_ratio_COUNTER/amm_of_lines_succ_synced)*100}%\n")
                
                file.write(f"-\n")
                
                file.write(f"RED PATH AMMOUNT: {red_path_ratio_COUNTER}\n")
                file.write(f"RED PATH PERCENTAGE: {(red_path_ratio_COUNTER/amm_of_lines_succ_synced)*100}%\n")
                
                file.write(f"RED PATH 3 AMMOUNT: {red_path_ratio_3_COUNTER}\n")
                file.write(f"RED PATH 3 PERCENTAGE: {(red_path_ratio_3_COUNTER/amm_of_lines_succ_synced)*100}%\n")
                
                file.write(f"RED PATH 4 AMMOUNT: {red_path_ratio_4_COUNTER}\n")
                file.write(f"RED PATH 4 PERCENTAGE: {(red_path_ratio_4_COUNTER/amm_of_lines_succ_synced)*100}%\n")
                
                file.write(f"SUM RED PATH'S AMMOUNT: {red_path_ratio_COUNTER+red_path_ratio_3_COUNTER+red_path_ratio_4_COUNTER}\n")
                file.write(f"SUM RED PATH'S PERCENTAGE: {((red_path_ratio_COUNTER+red_path_ratio_3_COUNTER+red_path_ratio_4_COUNTER)/amm_of_lines_succ_synced)*100}%\n")
                
                file.write(f"-\n")
                
                file.write(f"BLUE PATH AMMOUNT: {blue_path_ratio_COUNTER}\n")
                file.write(f"BLUE PATH PERCENTAGE (Ammount count *2): {((blue_path_ratio_COUNTER*2)/amm_of_lines_succ_synced)*100}%\n")
                
                file.write(f"BLUE PATH 3 AMMOUNT: {blue_path_ratio_3_COUNTER}\n")
                file.write(f"BLUE PATH 3 PERCENTAGE (Ammount count *3): {((blue_path_ratio_3_COUNTER*3)/amm_of_lines_succ_synced)*100}%\n")
                
                file.write(f"BLUE PATH 4 AMMOUNT: {blue_path_ratio_4_COUNTER}\n")     
                file.write(f"BLUE PATH 4 PERCENTAGE (Ammount count *4): {((blue_path_ratio_4_COUNTER*4)/amm_of_lines_succ_synced)*100}%\n")
                
                file.write(f"SUM BLUE PATH'S AMMOUNT: {blue_path_ratio_COUNTER+blue_path_ratio_3_COUNTER+blue_path_ratio_4_COUNTER}\n")     
                file.write(f"SUM BLUE PATH'S PERCENTAGE: {(((blue_path_ratio_COUNTER*2)+(blue_path_ratio_3_COUNTER*3)+(blue_path_ratio_4_COUNTER*4))/amm_of_lines_succ_synced)*100}%\n")
                
                file.write(f"-----\n")
    
    """
    ### Interpolate timestamps for lyrics lines that couldn't be matched ###
    main_chords_body_line_array_lyrics_with_index_and_timestamp = lerpNOTSYNCEDWithin(main_chords_body_line_array_lyrics_with_index_and_timestamp)
    # Don't call last and first interpolation, as there might be just chords at end and beginning of song, call rather with merged array to consider those chords
    # If you already call first and last lerp the function applies the last line with the length of the song, if after merging, there are chords or others further at the end, i can't be lerped anymore
    #main_chords_body_line_array_lyrics_with_index_and_timestamp = lerpNOTSYNCEDLastLines(main_chords_body_line_array_lyrics_with_index_and_timestamp, track_length_ms)
    #main_chords_body_line_array_lyrics_with_index_and_timestamp = lerpNOTSYNCEDFirstLines(main_chords_body_line_array_lyrics_with_index_and_timestamp)
    """    
    ############################################
    
    ### Consider all other lines from Ultimate Guitar that are probably not lyrics lines ### 
            
    main_chords_body_line_array_residual_with_index = [
        [index, line] for index, line in enumerate(main_chords_body_line_array)
        if (line == "" or "chord_span" in line or "[" in line or "]" in line or "|-" in line or "-|" in line or "capo" in line.lower() or "n.c." in line.lower() or "tuning" in line.lower())
    ]
    main_chords_body_line_array_residual_with_index_and_timestamp = [["NOTSYNCED", t[0], t[1]] for t in main_chords_body_line_array_residual_with_index]
    
    # Array of all synced and interpolated lyrics lines merged with unsynced residual lines
    merged_array, error_merging = mergeSyncedLyricsAndResidual(main_chords_body_line_array_residual_with_index_and_timestamp, main_chords_body_line_array_lyrics_with_index_and_timestamp)
    
    # Interpolate timestamps for residual lines with regard to synced lyrics lines timestamps    
    merged_array, error_lerping_1 = lerpNOTSYNCEDWithin(merged_array)
    merged_array, error_lerping_2 = lerpNOTSYNCEDLastLines(merged_array, track_length_ms)
    merged_array, error_lerping_3 = lerpNOTSYNCEDFirstLines(merged_array)
    
    # If error occured in merging or lerping return original source code without any timestamps and regard as not synced
    if (error_merging or error_lerping_1 or error_lerping_2 or error_lerping_3):
        return main_chords_body, True
    
    ############################################
    
    # Insert synced array into main chords body array
    for i in range (0, len(merged_array)):
        main_chords_body_line_array[merged_array[i][1]] = f'<span id="IS_SYNCED_AT:{merged_array[i][0]}">{main_chords_body_line_array[merged_array[i][1]]}</span>'    
                
    return "<br>".join(main_chords_body_line_array), False
    
# Replace NOTSCYNCED timestamps by interpolating with timestamps that exist in surrounding lines
def lerpNOTSYNCEDWithin(array_with_timestamps_to_be_lerped):       
    try:
        for timstamp in range (0, len(array_with_timestamps_to_be_lerped)):
            amm_of_cons_notsynced_lines = 0
            timestamp_adder = 0
            sorrounding_timestamp_after = 0
            sorrounding_timestamp_before = 0
            
            if array_with_timestamps_to_be_lerped[timstamp][0] == "NOTSYNCED":
                # First line not synced (consider in other algorithm in other according lerp function)
                if (timstamp == 0):
                    continue
                
                # Continue if previous line is not synced to skip and find next possible synced line
                if (array_with_timestamps_to_be_lerped[timstamp-1][0] == "NOTSYNCED"):
                    continue
                
                sorrounding_timestamp_before = int(float(str((array_with_timestamps_to_be_lerped[timstamp-1][0])).replace("\" class='ONE_LINE_OFF_IS_MORE_UNOFF'", "").replace("\" class='MORE_LINE_OFF_IS_ONE_UNOFF'", "").replace("\" class='LERP_LINE'", "").replace("\" class='ONE_LINE_OFF_IS_ONE_UNOFF'", "")))
                
                for first_synced_timestamp in range (timstamp, len(array_with_timestamps_to_be_lerped)):
                    # Is by one line NOTSYNCED consecutive also 2 already
                    amm_of_cons_notsynced_lines += 1
                    
                    # Last line not synced (consider in other algorithm in other according lerp function)
                    if array_with_timestamps_to_be_lerped[first_synced_timestamp][0] == "NOTSYNCED" and first_synced_timestamp == len(array_with_timestamps_to_be_lerped)-1:
                        amm_of_cons_notsynced_lines = 0
                        break
                    
                    # Found first timestamp that is not NOTSYNCED again
                    if array_with_timestamps_to_be_lerped[first_synced_timestamp][0] != "NOTSYNCED":
                        sorrounding_timestamp_after = int(float(str(array_with_timestamps_to_be_lerped[first_synced_timestamp][0]).replace("\" class='ONE_LINE_OFF_IS_MORE_UNOFF'", "").replace("\" class='MORE_LINE_OFF_IS_ONE_UNOFF'", "").replace("\" class='LERP_LINE'", "").replace("\" class='ONE_LINE_OFF_IS_ONE_UNOFF'", "")))
                        break
                
                # Last line not synced (consider in other algorithm in other according lerp function)
                if amm_of_cons_notsynced_lines == 0:
                    break
                
                # Calculate and insert lerp
                timestamp_adder = (sorrounding_timestamp_after - sorrounding_timestamp_before) / (amm_of_cons_notsynced_lines)
                for add_timestamp in range (1, amm_of_cons_notsynced_lines):
                    array_with_timestamps_to_be_lerped[timstamp + add_timestamp-1][0] = str(int(sorrounding_timestamp_before + (timestamp_adder * add_timestamp))) + "\" class='LERP_LINE'"
        
        return array_with_timestamps_to_be_lerped, False
    
    except:
        ic("lerpNOTSYNCEDWithin failed")
        return array_with_timestamps_to_be_lerped, True

# Replace NOTSCYNCED timestamps by interpolating timestamps between the last synced timestamp and the end of the track
def lerpNOTSYNCEDLastLines(array_with_timestamps_to_be_lerped, track_length_ms):        
    try:
        amm_of_cons_notsynced_lines = 0
        
        # If last line is NOTSYNCED
        if array_with_timestamps_to_be_lerped[len(array_with_timestamps_to_be_lerped)-1][0] == "NOTSYNCED":
            # Insert track length as timestamp into last line
            array_with_timestamps_to_be_lerped[len(array_with_timestamps_to_be_lerped)-1][0] = str(track_length_ms) + "\" class='LERP_LINE'"
            timestamp_before_index = 0
            
            # Iterate backwards until first not NOTSYNCED
            for i in range(len(array_with_timestamps_to_be_lerped)-2, -1, -1):
                amm_of_cons_notsynced_lines += 1
                if array_with_timestamps_to_be_lerped[i][0] != "NOTSYNCED":
                    timestamp_before_index = i
                    break
            
            sorrounding_timestamp_after = track_length_ms
            sorrounding_timestamp_before = int(float(str((array_with_timestamps_to_be_lerped[timestamp_before_index][0])).replace("\" class='ONE_LINE_OFF_IS_MORE_UNOFF'", "").replace("\" class='MORE_LINE_OFF_IS_ONE_UNOFF'", "").replace("\" class='LERP_LINE'", "").replace("\" class='ONE_LINE_OFF_IS_ONE_UNOFF'", "")))
            
            # Calculate and insert lerp
            timestamp_adder = (sorrounding_timestamp_after - sorrounding_timestamp_before) / (amm_of_cons_notsynced_lines)
            for add_timestamp in range (1, amm_of_cons_notsynced_lines):
                array_with_timestamps_to_be_lerped[timestamp_before_index+1 + add_timestamp-1][0] = str(int(sorrounding_timestamp_before + (timestamp_adder * add_timestamp))) + "\" class='LERP_LINE'"
        
        return array_with_timestamps_to_be_lerped, False
    
    except:
        print("lerpNOTSYNCEDLastLines failed")    
        return array_with_timestamps_to_be_lerped, True 

# Replace NOTSCYNCED timestamps by interpolating timestamps between the beginning of the track and the first synced timestamp 
def lerpNOTSYNCEDFirstLines(array_with_timestamps_to_be_lerped):    
    try:
        amm_of_cons_notsynced_lines = 0
        sorrounding_timestamp_before = 0
        
        if array_with_timestamps_to_be_lerped[0][0] == "NOTSYNCED":
            # Insert 0 ms as timestamp into first line
            array_with_timestamps_to_be_lerped[0][0] = "0" + "\" class='LERP_LINE'"
            
            # Iterate until first not NOTSYNCED   
            for i in range(1, len(array_with_timestamps_to_be_lerped)):    
                amm_of_cons_notsynced_lines += 1
                if array_with_timestamps_to_be_lerped[i][0] != "NOTSYNCED":  
                    sorrounding_timestamp_after = int(str((array_with_timestamps_to_be_lerped[i][0])).replace("\" class='ONE_LINE_OFF_IS_MORE_UNOFF'", "").replace("\" class='MORE_LINE_OFF_IS_ONE_UNOFF'", "").replace("\" class='LERP_LINE'", "").replace("\" class='ONE_LINE_OFF_IS_ONE_UNOFF'", ""))
                    break
            
            # Calculate and insert lerp
            timestamp_adder = (sorrounding_timestamp_after - sorrounding_timestamp_before) / (amm_of_cons_notsynced_lines)
            for add_timestamp in range (1, amm_of_cons_notsynced_lines):
                array_with_timestamps_to_be_lerped[1 + add_timestamp-1][0] = str(int(sorrounding_timestamp_before + (timestamp_adder * add_timestamp))) + "\" class='LERP_LINE'"
        
        return array_with_timestamps_to_be_lerped, False
    
    except:
        print("lerpNOTSYNCEDFirstLines failed")
        return array_with_timestamps_to_be_lerped, True
        
# Merge the synced lyrics array and the residual array        
def mergeSyncedLyricsAndResidual(main_chords_body_line_array_residual_with_index_and_timestamp, main_chords_body_line_array_lyrics_with_index_and_timestamp):        
    try:
        merged_array = []

        residual_index = 0
        lyrics_index = 0

        while residual_index < len(main_chords_body_line_array_residual_with_index_and_timestamp) and lyrics_index < len(main_chords_body_line_array_lyrics_with_index_and_timestamp):
            square_brackets_item = main_chords_body_line_array_residual_with_index_and_timestamp[residual_index]
            lyrics_item = main_chords_body_line_array_lyrics_with_index_and_timestamp[lyrics_index]

            if square_brackets_item[1] < lyrics_item[1]:
                merged_array.append(square_brackets_item)
                residual_index += 1
            else:
                merged_array.append(lyrics_item)
                lyrics_index += 1

        # Append any remaining elements from both arrays
        merged_array.extend(main_chords_body_line_array_residual_with_index_and_timestamp[residual_index:])
        merged_array.extend(main_chords_body_line_array_lyrics_with_index_and_timestamp[lyrics_index:])

        return merged_array, False
    
    except:
        print("mergeSyncedLyricsAndResidual failed")    
        return main_chords_body_line_array_residual_with_index_and_timestamp, True
        

# Delete Spotify cash when program stops (to achieve same functionality as /logout)
def cleanup():
    cache_file = '.cache'
    if os.path.exists(cache_file):
        os.remove(cache_file)            
atexit.register(cleanup)  


######## START FLASK SERVER ########        
if __name__ == '__main__':
    if (dev_or_prod == "DEVELOPMENT"):
        app.run(host="0.0.0.0", port=5000, debug=True)
