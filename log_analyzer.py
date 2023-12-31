import statistics


log_file_path = "logs/log__08_01_2024__21_12_06.txt"
with open(log_file_path, "r") as file:
    log = file.readlines()

def extract_playlist_info(log):
    playlist_info = None
    playlist_link = None

    for line in log:
        if "Playlist:" in line:
            playlist_info = line.split("Playlist:")[1].strip()
        elif "-> Link:" in line:
            playlist_link = line.split("-> Link:")[1].strip()

    return playlist_info, playlist_link

def calculate_song_ammount(log):
    songs_counter = 0

    for line in log:
        if "SONG: " in line:
            songs_counter += 1

    return songs_counter

def calculate_found_chords(log):
    found_chords_yes = 0
    found_chords_no = 0

    for line in log:
        if "FOUND ULTIMATE GUITAR CHORDS: YES" in line:
            found_chords_yes += 1
        elif "FOUND ULTIMATE GUITAR CHORDS: NO" in line:
            found_chords_no += 1

    return found_chords_yes, found_chords_no


def calculate_found_lyrics(log):
    found_lyrics_yes = 0
    found_lyrics_no = 0

    for line in log:
        if "FOUND LYRICS: YES" in line:
            found_lyrics_yes += 1
        elif "FOUND LYRICS: NO" in line:
            found_lyrics_no += 1

    return found_lyrics_yes, found_lyrics_no

def calculate_found_synced_lyrics(log):
    found_synced_lyrics_yes = 0
    found_synced_lyrics_no = 0

    for line in log:
        if "LYRICS ARE LINE SYNCED: YES" in line:
            found_synced_lyrics_yes += 1
        elif "LYRICS ARE LINE SYNCED: NO" in line:
            found_synced_lyrics_no += 1

    return found_synced_lyrics_yes, found_synced_lyrics_no



def calculate_mean_google_index(log):
    total_google_index = 0
    count_non_zero = 0

    for line in log:
        if "GOOGLE RESULT INDEX:" in line:
            index_value = int(line.split(":")[1].strip())
            if index_value != 0:
                total_google_index += index_value
                count_non_zero += 1

    if count_non_zero == 0:
        return 0  # Avoid division by zero

    average_google_index = total_google_index / count_non_zero
    return round(average_google_index, 2)

def calculate_median_google_index(log):
    index_values = []

    for line in log:
        if "GOOGLE RESULT INDEX:" in line:
            index_value = int(line.split(":")[1].strip())
            if index_value != 0:
                index_values.append(index_value)

    if not index_values:
        return 0  # Avoid division by zero

    median_google_index = statistics.median(index_values)
    return round(median_google_index, 2)

def calculate_syncable_songs(log):
    synced_songs_count = 0

    is_found_chords_yes = False
    is_found_lyrics_yes = False
    is_lyrics_synced_yes = False

    for line in log:
        if "FOUND ULTIMATE GUITAR CHORDS: YES" in line:
            is_found_chords_yes = True
        elif "FOUND LYRICS: YES" in line:
            is_found_lyrics_yes = True
        elif "LYRICS ARE LINE SYNCED: YES" in line:
            is_lyrics_synced_yes = True

        if is_found_chords_yes and is_found_lyrics_yes and is_lyrics_synced_yes:
            synced_songs_count += 1
            # Reset the flags for the next song
            is_found_chords_yes = False
            is_found_lyrics_yes = False
            is_lyrics_synced_yes = False

    return synced_songs_count


def calculate_mean_sync_ratio(log):
    total_sync_ratio = 0
    count_non_zero = 0

    for line in log:
        if "SYNC RATIO:" in line:
            sync_ratio_str = line.split(":")[1].strip().replace('%', '')
            try:
                sync_ratio_value = float(sync_ratio_str)
                total_sync_ratio += sync_ratio_value
                count_non_zero += 1
            except ValueError:
                print(f"Error converting '{sync_ratio_str}' to float. Skipping this line.")

    if count_non_zero == 0:
        return 0  # Avoid division by zero

    average_sync_ratio = total_sync_ratio / count_non_zero
    return round(average_sync_ratio, 2)

def calculate_median_sync_ratio(log):
    sync_ratios = []

    for line in log:
        if "SYNC RATIO:" in line:
            sync_ratio_str = line.split(":")[1].strip().replace('%', '')
            try:
                sync_ratio_value = float(sync_ratio_str)
                sync_ratios.append(sync_ratio_value)
            except ValueError:
                print(f"Error converting '{sync_ratio_str}' to float. Skipping this line.")

    if not sync_ratios:
        return 0  # Avoid division by zero

    median_sync_ratio = statistics.median(sync_ratios)
    return round(median_sync_ratio, 2)

#################### 

playlist_info, playlist_link = extract_playlist_info(log)
print("Playlist Name:", playlist_info)
print("Playlist Link:", playlist_link)

song_counter = calculate_song_ammount(log)
print("Playlist Songs:", song_counter)

print("-----")

found_chords_yes, found_chords_no = calculate_found_chords(log)
print("Found Chords: YES: {}, NO: {}".format(found_chords_yes, found_chords_no))

mean_google_index = calculate_mean_google_index(log)
print("Mean Google Chords Result Index (Applied to song with found chords):", mean_google_index)

median_google_inedx = calculate_median_google_index(log)
print("Median Google Chords Result Index (Applied to song with found chords):", median_google_inedx)

print("-----")

found_lyrics_yes, found_lyrics_no = calculate_found_lyrics(log)
print("Found Lyrics: YES: {}, NO: {}".format(found_lyrics_yes, found_lyrics_no))

found_synced_lyrics_yes, found_synced_lyrics_no = calculate_found_synced_lyrics(log)
print("Found Line Synced Lyrics: YES: {}, NO: {}".format(found_synced_lyrics_yes, found_synced_lyrics_no))

print("-----")

syncable_songs_count = calculate_syncable_songs(log)
print("Songs that are syncable (i.e. FOUND CHORDS: YES, FOUND LYRICS: YES, LYRICS ARE LINE SYNCED: YES):", syncable_songs_count)

mean_sync_ratio = calculate_mean_sync_ratio(log)
print("Mean Sync Ratio: ", mean_sync_ratio, "%", sep="")

median_sync_ratio = calculate_median_sync_ratio(log)
print("Median Sync Ratio: ", median_sync_ratio, "%", sep="")


