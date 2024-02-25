from fuzzywuzzy import fuzz, process
from icecream import ic

official_lyrics_line = 'kitten'
unofficial_lyrics_line = 'sitting'

ic(fuzz.ratio(official_lyrics_line, unofficial_lyrics_line))