main_chords_body_line_array_squarebrackets_with_index_and_timestamp = [
    ['NOTSYNCED', 0, '[Intro]'],
    ['NOTSYNCED', 9, '[Verse 1]'],
    ['NOTSYNCED', 29, '[Chorus]'],
    ['NOTSYNCED', 48, '[Instrumental]'],
    ['NOTSYNCED', 57, '[Verse 2]'],
    ['NOTSYNCED', 77, '[Chorus]'],
    ['NOTSYNCED', 96, '[Instrumental]'],
    ['NOTSYNCED', 104, '[Verse 3]'],
    ['NOTSYNCED', 116, '[Chorus]']
]

main_chords_body_line_array_lyrics_with_index_and_timestamp = [
    [21290, 12, '  I wanna take you somewhere so you know I care,'],
    [25870, 14, 'but it&#039;s so cold and I don&#039;t know where'],
    [29850, 16, 'I brought you daffodils, on a pretty string,'],
    [33940, 18, 'but they won&#039;t flower like they did last spring'],
    [41910, 20, '  And I wanna kiss you, make you feel alright,'],
    [46150, 22, 'but I&#039;m just so tired to share my nights'],
    [50200, 24, 'I wanna cry and I wanna love'],
    [54280, 26, 'But all my tears have been used up'],
    [62360, 32, '  On another love, another love'],
    [66880, 34, 'All my tears have been used up,'],
    [70540, 36, 'on another love, another love'],
    [75080, 38, 'All my tears have been used up,'],
    [78820, 40, 'on another love, another love'],
    [83350, 42, 'All my tears have been used uuuhuuuhuuup']
]

def mergeSyncedLyricsAndResidual(main_chords_body_line_array_squarebrackets_with_index_and_timestamp, main_chords_body_line_array_lyrics_with_index_and_timestamp):
    merged_array = []

    square_brackets_index = 0
    lyrics_index = 0

    while square_brackets_index < len(main_chords_body_line_array_squarebrackets_with_index_and_timestamp) and lyrics_index < len(main_chords_body_line_array_lyrics_with_index_and_timestamp):
        square_brackets_item = main_chords_body_line_array_squarebrackets_with_index_and_timestamp[square_brackets_index]
        lyrics_item = main_chords_body_line_array_lyrics_with_index_and_timestamp[lyrics_index]

        if square_brackets_item[1] < lyrics_item[1]:
            merged_array.append(square_brackets_item)
            square_brackets_index += 1
        else:
            merged_array.append(lyrics_item)
            lyrics_index += 1

    # Append any remaining elements from both arrays
    merged_array.extend(main_chords_body_line_array_squarebrackets_with_index_and_timestamp[square_brackets_index:])
    merged_array.extend(main_chords_body_line_array_lyrics_with_index_and_timestamp[lyrics_index:])

    return merged_array

print(mergeSyncedLyricsAndResidual(main_chords_body_line_array_squarebrackets_with_index_and_timestamp, main_chords_body_line_array_lyrics_with_index_and_timestamp))
