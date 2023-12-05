from fuzzywuzzy import fuzz, process

title = 'Sorry About The Carpet Chords by Agar Agar '
track_name = 'Sorry About The Carpet Remastered 2011'
artist_name = 'Agar Agar 2'

print(fuzz.partial_ratio(title, track_name))