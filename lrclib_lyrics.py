"""
LRCLIB-based lyrics retrieval for ChordSync
Provides another method for fetching synced lyrics
(Module created by Nicholas after Spotify Lyrics retrieval stopped working)
"""
 
import os
import json
import re
import requests
import time
from urllib.parse import quote
from icecream import ic
 
class LRCLIBLyrics:
    def __init__(self):
        self.base_url = "https://lrclib.net/api"
        self.client_name = "ChordSync"
        self.client_version = "1.0.0"
        
    def get_lyrics(self, track_id, artist_name, track_name, album_name=None, duration_ms=None):
        """
        Get lyrics for a song using LRCLIB API
        
        Args:
            track_id: Spotify track ID (used for caching)
            artist_name: Name of the artist
            track_name: Name of the track
            album_name: Name of the album (optional)
            duration_ms: Duration of the track in milliseconds (optional)
            
        Returns:
            A dictionary containing lyrics with timestamps
        """
        try:
            # Clean track and artist names to improve search
            clean_track_name = self._clean_name(track_name)
            clean_artist_name = self._clean_name(artist_name)
            
            # Convert duration from ms to seconds if provided
            duration_sec = None
            if duration_ms:
                duration_sec = duration_ms # keep using ms, as it is more accurate and this make things clickable in the UI
            
            # First try the GET method with specific track details
            lyrics_data = self._get_lyrics_by_details(clean_track_name, clean_artist_name, album_name, duration_sec)
            
            # If not found, try the search method as fallback
            if not lyrics_data:
                ic("Track not found with direct query, trying search...")
                lyrics_data = self._search_lyrics(clean_track_name, clean_artist_name, album_name)
            
            # If we found lyrics data
            if lyrics_data:
                # Check if synced lyrics are available
                if lyrics_data.get("syncedLyrics"):
                    synced_lyrics = lyrics_data.get("syncedLyrics", "")
                    return self._parse_synced_lyrics(synced_lyrics)
                # Fallback to plain lyrics if synced aren't available
                elif lyrics_data.get("plainLyrics"):
                    plain_lyrics = lyrics_data.get("plainLyrics", "")
                    return self._create_unsynced_response(plain_lyrics)
            
            # Default return for no lyrics found
            return {"lyrics": {"syncType": "UNSYNCED", "lines": []}}
            
        except Exception as e:
            ic(f"Error fetching lyrics with LRCLIB: {e}")
            # Return an empty result that mimics the structure expected by the app
            return {"lyrics": {"syncType": "UNSYNCED", "lines": []}}
    
    def _clean_name(self, name):
        """Clean up track or artist name for better API matching"""
        if not name:
            return ""
        
        # Remove remasters, versions, feat. artists, etc.
        name = re.sub(r'\s-\s.*?(remaster|version|feat|ft\.|\(with|live|acoustic).*?$', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\(.*?(remaster|version|feat|ft\.|\(with|live|acoustic).*?\)', '', name, flags=re.IGNORECASE)
        
        return name.strip()
    
    def _get_lyrics_by_details(self, track_name, artist_name, album_name=None, duration=None):
        """Use the direct GET API with track details"""
        query_params = {
            "track_name": track_name,
            "artist_name": artist_name
        }
        
        # Add optional parameters if available
        if album_name:
            query_params["album_name"] = album_name
        if duration:
            query_params["duration"] = duration
        
        # Build query string
        query_string = "&".join([f"{k}={quote(str(v))}" for k, v in query_params.items()])
        url = f"{self.base_url}/get?{query_string}"
        
        # Make the request
        headers = {
            "Lrclib-Client": f"{self.client_name} v{self.client_version}"
        }
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                ic(f"Track not found with details: {track_name} by {artist_name}")
                return None
            else:
                ic(f"Error from LRCLIB API: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            ic(f"Request error: {e}")
            return None
    
    def _search_lyrics(self, track_name, artist_name, album_name=None):
        """Use the search API as fallback"""
        query_params = {}
        
        # Add as many specific fields as possible for better results
        if track_name:
            query_params["track_name"] = track_name
        if artist_name:
            query_params["artist_name"] = artist_name
        if album_name:
            query_params["album_name"] = album_name
        
        # If we don't have specific fields, use a generic query
        if not query_params:
            combined = f"{track_name} {artist_name}".strip()
            if combined:
                query_params["q"] = combined
        
        # Build query string
        query_string = "&".join([f"{k}={quote(str(v))}" for k, v in query_params.items()])
        url = f"{self.base_url}/search?{query_string}"
        
        # Make the request
        headers = {
            "Lrclib-Client": f"{self.client_name} v{self.client_version}"
        }
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                results = response.json()
                
                # Return the first result if any are found
                if results and len(results) > 0:
                    # Try to find the best match
                    for result in results:
                        # Check if this is likely our track
                        if (self._similarity_check(result.get("trackName", ""), track_name) and 
                            self._similarity_check(result.get("artistName", ""), artist_name)):
                            return result
                    
                    # If no good match found, return the first result
                    return results[0]
                
            return None
        except Exception as e:
            ic(f"Search request error: {e}")
            return None
    
    def _similarity_check(self, str1, str2):
        """Simple check to see if strings are similar enough"""
        if not str1 or not str2:
            return False
            
        # Convert to lowercase and remove special characters
        s1 = re.sub(r'[^\w\s]', '', str1.lower())
        s2 = re.sub(r'[^\w\s]', '', str2.lower())
        
        # Check if one contains the other
        return s1 in s2 or s2 in s1
    
    def _parse_synced_lyrics(self, synced_lyrics_text):
        """Parse LRC format into our required format"""
        if not synced_lyrics_text:
            return {"lyrics": {"syncType": "UNSYNCED", "lines": []}}
        
        lines = []
        # Match timestamps like [00:15.32] or [00:15:32]
        pattern = r'\[([\d:\.]+)\](.*)'
        
        for line in synced_lyrics_text.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            match = re.match(pattern, line)
            if match:
                timestamp_str = match.group(1)
                text = match.group(2).strip()
                
                # Skip empty lines or instrumental markers
                if not text or text == '♪' or text == '♫':
                    continue
                
                # Convert timestamp to milliseconds
                try:
                    # Handle both [mm:ss.xx] and [mm:ss:xx] formats
                    timestamp_str = timestamp_str.replace(':', '.', 1)
                    parts = timestamp_str.split('.')
                    
                    if len(parts) == 2:  # Format: mm.ss
                        minutes, seconds = map(float, parts)
                        ms = int((minutes * 60 + seconds) * 1000)
                    elif len(parts) == 3:  # Format: mm.ss.xx
                        minutes, seconds, fraction = map(float, parts)
                        ms = int((minutes * 60 + seconds) * 1000 + fraction * 10)
                    else:
                        continue  # Invalid format
                        
                    lines.append({
                        "startTimeMs": str(ms),
                        "words": text
                    })
                except Exception as e:
                    ic(f"Error parsing timestamp: {timestamp_str} - {e}")
                    continue
        
        # Sort lines by timestamp
        lines.sort(key=lambda x: int(x["startTimeMs"]))
        
        return {
            "lyrics": {
                "syncType": "LINE_SYNCED" if lines else "UNSYNCED",
                "lines": lines
            }
        }
    
    def _create_unsynced_response(self, plain_lyrics):
        """Convert plain lyrics to our format"""
        if not plain_lyrics:
            return {"lyrics": {"syncType": "UNSYNCED", "lines": []}}
        
        # Split by line and filter out empty lines
        lyrics_lines = [line.strip() for line in plain_lyrics.split('\n') if line.strip()]
        
        return {
            "lyrics": {
                "syncType": "UNSYNCED",
                "lines": lyrics_lines
            }
        }
    
    def adjust_timestamps(self, lyrics_data, track_duration_ms):
        """
        Adjust timestamps to match the actual song duration
        
        Args:
            lyrics_data: Lyrics data with timestamps
            track_duration_ms: Actual duration of the track in milliseconds
            
        Returns:
            Updated lyrics data with adjusted timestamps
        """
        if not lyrics_data or "lyrics" not in lyrics_data or "lines" not in lyrics_data["lyrics"]:
            return lyrics_data
        
        lines = lyrics_data["lyrics"]["lines"]
        if not lines:
            return lyrics_data
        
        # For unsynced lyrics, no adjustment needed
        if lyrics_data["lyrics"]["syncType"] == "UNSYNCED":
            return lyrics_data
            
        # Calculate the scaling factor
        try:
            last_timestamp = max(int(line["startTimeMs"]) for line in lines)
            if last_timestamp <= 0:
                return lyrics_data
                
            # Adjust scaling to ensure lyrics don't extend beyond the track
            scaling_factor = (track_duration_ms * 0.95) / last_timestamp
            
            # Adjust timestamps
            for line in lines:
                line["startTimeMs"] = str(int(int(line["startTimeMs"]) * scaling_factor))
        except Exception as e:
            ic(f"Error adjusting timestamps: {e}")
            
        return lyrics_data