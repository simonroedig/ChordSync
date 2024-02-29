```
   _____ _                   _  _____                  
  / ____| |                 | |/ ____|                 
 | |    | |__   ___  _ __ __| | (___  _   _ _ __   ___ 
 | |    | '_ \ / _ \| '__/ _` |\___ \| | | | '_ \ / __|
 | |____| | | | (_) | | | (_| |____) | |_| | | | | (__ 
  \_____|_| |_|\___/|_|  \__,_|_____/ \__, |_| |_|\___|
                                       __/ |           
                                      |___/  
```
<img src="/for_git_readme/afterstudy_chordsync.png" alt="ChordSync Snapshot" width="100%" height="100%">

## User Story:
"As a guitarist who enjoys playing along with songs, I often find it frustrating that my chord sheets require constant scrolling and manual adjustment to stay synchronized with the song, disrupting my playing flow. Additionally, I frequently play songs from my Spotify playlist, which necessitates actively searching and finding the correct chord sheets after each song. Seeking a solution, I discovered ChordSync, a revolutionary software designed to streamline the play-along experience for guitarists. With ChordSync's instant connection to Spotify, I can effortlessly select a song and have the corresponding chord sheet immediately retreived and displayed from Ultimate Guitar via a refined search algorithm. The innovative auto-scrolling algorithm ensures bidirectional synchronization between the chord sheet and the song itself. Whether navigating different sections in the song's timeline or on the chord sheet, ChordSync seamlessly adjusts, eliminating the need for manual corrections and enabling effortless song navigation. Moreover, with the repeat functionality, I can define specific sections in the chord sheet and practice them repeatedly by simply clicking the lyrics or chords, allowing for focused practice on particular parts of the song. To ensure ChordSync displays only syncable songs, I can activate the functionality to instruct Spotify to exclusively play and skip to songs that ChordSync can successfully process. Furthermore, ChordSync integrates standard guitar tool functionalities like capo settings, chord preferences, BPM and key display, and even a tuner, with the added benefit of persisting user preferences across songs, automatically applying them to newly parsed chord sheets. With ChordSync, not only can I play along with my favorite songs effortlessly, but I can also discover and explore new music recommended by Spotify while simultaneously improving my guitar skills."

## Key features of ChordSync:
- **1. Spotify Connection:** select a song and have the corresponding chord sheet immediately retreived and displayed from Ultimate-Guitar

- **2. Bi-Directional Auto-Scroll Algorithm:** Whether navigating different sections in the song's timeline or on the chord sheet, ChordSync seamlessly adjusts, eliminating the need for manual scrolling corrections to keep in sync with the song

- **3. Repeat Functionality:** Define specific sections to be repeated via simple clicks into the chord-sheet after toggling this feature

- **4. Play Only Syncable Songs:** Instructs Spotify to play only songs that ChordSync can successfully synchronize and skipping unsyncable songs

- **5. Integrated Guitar Tools:** Access standard functionalities such as capo settings, chord preferences, BPM and key display, and a tuner, with user preferences persisting across songs 

## How to install ChordSync:
- **1.** Install `python`: https://phoenixnap.com/kb/how-to-install-python-3-windows
- **2.** Optional: install a `Code-Editor` like Visual Studio Code
- **3.** `Download` this `repository` (main branch), (e.g. click green "<> Code" button on GitHub, download ZIP and unpack)
- **4.** Install `dependencies`: Open a terminal in the ...\ChordSync-main folder, and run:
```
pip install -r requirements.txt
```
- **5.** `Locate the env.txt` file and `follow its inctructions`, the files name afterwards must be solely `.env`, read next points to understand what
to paste exactly into this file
- **6.** Create an `Spotify "App"`:
   - ChordSync connects to your Spotify account and uses the `Spotify API` (you must have Spotify `Premium!`)
   - Go to: https://developer.spotify.com/dashboard and `create a new App` (click "Create App")
   - Paste http://localhost:5000/callback into the `Redirect URIs` field, enter your desired name and description
   - Go to the created Apps' `Settings`, here you will find the `Client ID` and `Client secret` (click "view client secret")
   - `Paste` both values `to the .env file` at the `respective places`
- **7.** Set-up `Google Search API`:
   - To find and retreive the chord sheets from Ultimate-Guitar, the Search API from Google is used
   - You can request this API `100x per day for free`, meaning you can play up to 100 songs per day with ChordSync. You `will not be automatically charged` if you exceed this limit unless you register for a billing plan, ChordSync will inform you when your daily Quota is exceeded
   - Go to: https://developers.google.com/custom-search/v1/overview and click `Get a Key` at the `API Key section`, the project name doesn't matter
   - Click to `show the API Key`, `paste` this value `to the .env file` at `GOOGLE_API_KEY`
   - Go to: https://programmablesearchengine.google.com/controlpanel/all and `create a new search engine`
   - Choose to `search the whole web`, the search engine name doesn't matter
   - Don't copy the "script" code, but click on adjust/customize and `locate and copy the search engine ID`
   - `Paste` this value `to the .env file ` at `GOOGLE_SEARCH_ENGINE_ID`
- **8.** ChordSyncs' main algorithm is based on Musixmatchs lyrics that is also the lyrics you find when you listen to a song on spotify,
to retreive these lyrics you need a `sp_dc cookie` from spotify:
   - A general `detailed guide to retreive this cookie` was provided by [akashrchandran](https://github.com/akashrchandran/akashrchandran) -> [here](https://github.com/akashrchandran/syrics/wiki/Finding-sp_dc).
   - `Paste` the (very long) content of the sp_dc cookie `to the .env file` at `SP_DC_COOKIE`
- **9.** The setup should be complete, the main `entry point of ChordSync` is the file `App.py`, which you can either `run with your Code-Editor/IDE` or via `clicking App.py directly`
   - It will open a terminal with some information, you should see the following:
   ```
   .
   .
   WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
   * Running on all addresses (0.0.0.0)
   * Running on http://127.0.0.1:5000 (*1)
   * Running on http://192.168.2.100:5000 (*2)
   Press CTRL+C to quit
   .
   .
   ```
   - The adresses `(*1, *2)` might be different for you
   - To open ChordSync `paste one of those IP-Adresses into your browser`:
   - *1 is the Loopback IP-Adress, it also resolves to http://localhost:5000/, with it you can access ChordSync only from the computer you ran it from
   - *2 is the private IP-Adress of the device you ran it from, you can ALSO paste this IP into other devices' browser in your network and will see ChordSync
   - Feel free to set a browser bookmark to access ChordSync via the IP's quicker, however *2 might change depending on your router settings
   - You can `stop ChordSync with CTRL+C in your terminal`, you have to redo step 9. if you want to run ChordSync again
- **10.** If you have `any troubles` with installing and running, `feel free to reach out to me`

<p>ChordSync © 2024 by Simon Rödig is licensed under CC BY-NC-ND 4.0.</p>
<p>To view a copy of this license, visit http://creativecommons.org/licenses/by-nc-nd/4.0/</p>