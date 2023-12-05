from icecream import ic

ha = [1,2,3,4,5]

weil = 10
counter = 0
insert_hit = 0

while counter < weil:
    for unofficial_lyrics_line in range (insert_hit, len(ha)):
        ic(unofficial_lyrics_line)
        if (ha[unofficial_lyrics_line] == 2):
            ic("inhalt 2")
            insert_hit = unofficial_lyrics_line + 2
            break
        
    counter += 1