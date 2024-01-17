import numpy as np
import pandas as pd
import statistics
import matplotlib.pyplot as plt

"""
This python script/file depcits the result and analysis of my study.
- Some results or values were already calculated before within Qualtrics (Tool for survey).
https://www.qualtrics.com/

The data was derived from 5 endpoints:
Pre Registration:
1. (Qualtrics Link) Name, Age, Online/Person, Mail, Guitar Experience, Preferred Chord Tool, 
Music Provider, Music Genre/Artist, Appointment Booking

Main Study:
2. (Qualtrics Link)  Used to get consent for the main study (Just agree or disagree and name)
3. (Qualtrics Link)  Questionnaire about the user's playing experience using his preferred chord tool
4. (Qualtrics Link)  Questionnaire about the user's playing experience using ChordSync
5. Questions asked withing semi-structured interviews at differents times of the main study

P<X> in variable names refers to the participant number
"""

### Via 1.
participant_ammount = 6

age_mean = 0 
experience_mean = 0

music_provider = [
    ("Spotify"), 
    ("Spotify"),
    ("TouTube", "Spotify"),
    ("Spotify", "YouTube", "Amazon Music"),
    ("Spotify", "YouTube"),
    ("Spotify")
]
music_provider_names = ["Spotify", "YouTube", "Amazon Music"]
music_provider_count = [6, 3, 1]
plt.bar(music_provider_names, music_provider_count)
plt.xlabel("Music Provider")
plt.ylabel("Ammount")
plt.show()
    
chord_note_tool = [
    ("Ultimate Guitar", "Ultimate Guitar Pro", "Songsterr",  "911Tabs"), 
    ("Ultimate Guitar", "Guitar Chords and Tabs"),
    ("Ultimate Guitar"),
    ("Ultimate Guitar", "911Tabs", "Yousician"),
    ("iReal"),
    ("Ultimate Guitar", "Songsterr", "e-chords")
]
chord_note_tool_names = ["Ultimate Guitar", "Songsterr", "911Tabs", "Ultimate Guitar Pro", "Guitar Chords and Tabs", "Yousician", "iReal", "e-chords"]
chord_note_tool_count = [5, 2, 2, 1, 1, 1, 1, 1]
plt.bar(chord_note_tool_names, chord_note_tool_count)
plt.xlabel("Chord/Note Tool")
plt.ylabel("Ammount")
plt.show()

### Via 5.
how_long_played_instrument_for = [12.5, 5, 3, 20, 50, 10] # in years
print(statistics.mean(how_long_played_instrument_for))

