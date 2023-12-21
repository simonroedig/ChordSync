from fuzzywuzzy import fuzz, process
from icecream import ic

official_lyrics_line = 'This is a test'
unofficial_lyrics_line = 'This is a tost'

ic(fuzz.ratio(official_lyrics_line, unofficial_lyrics_line))