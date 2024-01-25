import statistics

### LOG FILE SOURCE ###
log_file_path = "logs/easy_songs_to_learn_on_guitar.txt"
with open(log_file_path, "r") as file:
    log = file.readlines()



### PLAYLIST INFO ###
def extract_playlist_info(log):
    playlist_info = None
    playlist_creator = None
    playlist_likes = None
    playlist_timestamp = None
    playlist_link = None


    for line in log:
        if "Playlist Name:" in line:
            playlist_info = line.split("Playlist Name:")[1].strip()
            
        elif "Playlist Created by:" in line:
            playlist_creator = line.split("Playlist Created by:")[1].strip()
            
        elif "Playlist Likes:" in line:
            playlist_likes = line.split("Playlist Likes:")[1].strip()
            
        elif "Playlist Timestamp:" in line:
            playlist_timestamp = line.split("Playlist Timestamp:")[1].strip()
            
        elif "-> Link:" in line:
            playlist_link = line.split("-> Link:")[1].strip()

    return playlist_info, playlist_creator, playlist_likes, playlist_timestamp, playlist_link

def calculate_song_ammount(log):
    songs_counter = 0

    for line in log:
        if "SONG: " in line:
            songs_counter += 1

    return songs_counter



### CHORD SOURCE INFORMATION ###
def calculate_found_chords(log):
    found_chords_yes = 0
    found_chords_no = 0

    for line in log:
        if "FOUND ULTIMATE GUITAR CHORDS: YES" in line:
            found_chords_yes += 1
        elif "FOUND ULTIMATE GUITAR CHORDS: NO" in line:
            found_chords_no += 1

    return found_chords_yes, found_chords_no

def calculate_mean_google_index(log):
    index_values = []

    for line in log:
        if "GOOGLE RESULT INDEX:" in line:
            index_value = int(line.split(":")[1].strip())
            if index_value != 0:
                index_values.append(index_value)

    if not index_values:
        return 0  # Avoid division by zero
    
    average_google_index = sum(index_values) / len(index_values)
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



### LYRICS SOURCE INFORMATION ###
def calculate_found_lyrics(log):
    found_lyrics_yes = 0
    found_lyrics_no = 0

    for line in log:
        if "FOUND LYRICS: YES" in line:
            found_lyrics_yes += 1
        elif "FOUND LYRICS: NO" in line:
            found_lyrics_no += 1

    return found_lyrics_yes, found_lyrics_no

def calculate_lyrics_found_and_not_line_synced(log):
    count_occurrences = 0

    for i in range(len(log) - 1):
        if log[i].strip() == 'FOUND LYRICS: YES' and log[i + 1].strip() == 'LYRICS ARE LINE SYNCED: NO':
            count_occurrences += 1

    return count_occurrences

def calculate_lyrics_found_and_line_synced(log):
    count_occurrences = 0

    for i in range(len(log) - 1):
        if log[i].strip() == 'FOUND LYRICS: YES' and log[i + 1].strip() == 'LYRICS ARE LINE SYNCED: YES':
            count_occurrences += 1

    return count_occurrences

def calculate_lyrics_not_found_but_line_synced(log):
    count_occurrences = 0

    for i in range(len(log) - 1):
        if log[i].strip() == 'FOUND LYRICS: NO' and log[i + 1].strip() == 'LYRICS ARE LINE SYNCED: YES':
            count_occurrences += 1

    return count_occurrences



### SONGS THAT ARE SYNCABLE ###
def calculate_syncable_songs_old_wrong(log):
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

def calculate_syncable_songs_new(log):
    sync_ratio_count = 0
    for line in log:
        if "SYNC RATIO:" in line:
            sync_ratio_count += 1
    return sync_ratio_count

def calculate_syncable_songs_new2(log):
    condition_count = 0

    for i in range(len(log)):
        if "FOUND ULTIMATE GUITAR CHORDS: YES" in log[i] and "FOUND LYRICS: YES" in log[i + 4] and "LYRICS ARE LINE SYNCED: YES" in log[i + 5]:
            condition_count += 1
    return condition_count

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

def calculate_mean_amnt_of_lyrics(log):
    amnt_of_lyrics_list = []
    successfully_synced_lyrics_list = []

    for line in log:
        if "AMMOUNT OF MUSIXMATCH LYRICS TO SYNC (without empty or note):" in line:
            amnt_of_lyrics_str = line.split(":")[1].strip()
            try:
                amnt_of_lyrics_value = int(amnt_of_lyrics_str)
                amnt_of_lyrics_list.append(amnt_of_lyrics_value)
            except ValueError:
                print(f"Error converting '{amnt_of_lyrics_str}' to int. Skipping this line.")

        elif "AMMOUNT OF SUCCESSFULLY SYNCED MUSIXMATCH LYRICS:" in line:
            synced_lyrics_str = line.split(":")[1].strip()
            try:
                synced_lyrics_value = int(synced_lyrics_str)
                successfully_synced_lyrics_list.append(synced_lyrics_value)
            except ValueError:
                print(f"Error converting '{synced_lyrics_str}' to int. Skipping this line.")

    if not amnt_of_lyrics_list or not successfully_synced_lyrics_list:
        return 0, 0  # Avoid division by zero

    mean_amnt_of_lyrics = round(statistics.mean(amnt_of_lyrics_list), 2)
    mean_successfully_synced_lyrics = round(statistics.mean(successfully_synced_lyrics_list), 2)

    return mean_amnt_of_lyrics, mean_successfully_synced_lyrics

def calculate_median_amnt_of_lyrics(log):
    amnt_of_lyrics_list = []
    successfully_synced_lyrics_list = []

    for line in log:
        if "AMMOUNT OF MUSIXMATCH LYRICS TO SYNC (without empty or note):" in line:
            amnt_of_lyrics_str = line.split(":")[1].strip()
            try:
                amnt_of_lyrics_value = int(amnt_of_lyrics_str)
                amnt_of_lyrics_list.append(amnt_of_lyrics_value)
            except ValueError:
                print(f"Error converting '{amnt_of_lyrics_str}' to int. Skipping this line.")

        elif "AMMOUNT OF SUCCESSFULLY SYNCED MUSIXMATCH LYRICS:" in line:
            synced_lyrics_str = line.split(":")[1].strip()
            try:
                synced_lyrics_value = int(synced_lyrics_str)
                successfully_synced_lyrics_list.append(synced_lyrics_value)
            except ValueError:
                print(f"Error converting '{synced_lyrics_str}' to int. Skipping this line.")

    if not amnt_of_lyrics_list or not successfully_synced_lyrics_list:
        return 0, 0  # Avoid division by zero

    median_amnt_of_lyrics = round(statistics.median(amnt_of_lyrics_list), 2)
    median_successfully_synced_lyrics = round(statistics.median(successfully_synced_lyrics_list), 2)

    return median_amnt_of_lyrics, median_successfully_synced_lyrics


### PATHS ###
def calculate_mean_path_percentage(log, striiing):
    total_sync_ratio = 0
    count_non_zero = 0

    for line in log:
        if striiing in line:
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

def calculate_median_path_percentage(log, striiing):
    sync_ratios = []

    for line in log:
        if striiing in line:
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

playlist_info, playlist_creator, playlist_likes, playlist_timestamp, playlist_link = extract_playlist_info(log)
print("Playlist Name:", playlist_info)
print("Playlist Creator:", playlist_creator)
print("Playlist Likes:", playlist_likes)
print("Playlist Timestamp:", playlist_timestamp)
print("-> Playlist Link:", playlist_link)

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

lyrics_found_and_line_synced = calculate_lyrics_found_and_line_synced(log)
print("-> Found Lyrics AND Lyrics are Line Synced:", lyrics_found_and_line_synced)

lyrics_found_and_not_line_synced = calculate_lyrics_found_and_not_line_synced(log)
print("-> Found Lyrics but Lyrics are NOT Line Synced:", lyrics_found_and_not_line_synced)

lyrics_not_found_but_line_synced = calculate_lyrics_not_found_but_line_synced(log)
print("-> Found NO Lyrics but Lyrics are Line Synced (Should be 0):", lyrics_not_found_but_line_synced)

print("-----")

syncable_songs_count = calculate_syncable_songs_new(log)
print("Songs that are syncable (Found Chords and Line Synced Lyrics):", syncable_songs_count)

mean_sync_ratio = calculate_mean_sync_ratio(log)
print("-> Mean Successfully Synced Lines Ratio: ", mean_sync_ratio, "%", sep="")

median_sync_ratio = calculate_median_sync_ratio(log)
print("-> Median Successfully Synced Lines Ratio: ", median_sync_ratio, "%", sep="")

mean_amnt_of_lyrics, mean_successfully_synced_lyrics = calculate_mean_amnt_of_lyrics(log)
print(f"-> Mean Ammount of MusixMatch Lyrics Lines to sync (without Note symbol or empty string): {mean_amnt_of_lyrics}")
print(f"-> Mean Ammount of successfully synced MusixMatch Lyrics Lines: {mean_successfully_synced_lyrics}")

median_amnt_of_lyrics, median_successfully_synced_lyrics = calculate_median_amnt_of_lyrics(log)
print(f"-> Median Ammount of MusixMatch Lyrics Lines to sync (without Note symbol or empty string): {median_amnt_of_lyrics}")
print(f"-> Median Ammount of successfully synced MusixMatch Lyrics Lines: {median_successfully_synced_lyrics}")

###########################################################################################################

print("-----")

print("The Paths' percentages are in regard to the successfully synced lines")
print("---")

mean_green_path_percentage = calculate_mean_path_percentage(log, "GREEN PATH PERCENTAGE:")
print("-> Mean Green Path: ", mean_green_path_percentage, "%", sep="")

median_green_path_percentage = calculate_median_path_percentage(log, "GREEN PATH PERCENTAGE:")
print("-> Median Green Path: ", median_green_path_percentage, "%", sep="")

print("---")

mean_red_path_percentage = calculate_mean_path_percentage(log, "RED PATH PERCENTAGE:")
print("Mean Red Path: ", mean_red_path_percentage, "%", sep="")

median_red_path_percentage = calculate_median_path_percentage(log, "RED PATH PERCENTAGE:")
print("Median Red Path: ", median_red_path_percentage, "%", sep="")

mean_red_path_3_percentage = calculate_mean_path_percentage(log, "RED PATH 3 PERCENTAGE:")
print("Mean Red 3 Path: ", mean_red_path_3_percentage, "%", sep="")

median_red_path_3_percentage = calculate_median_path_percentage(log, "RED PATH 3 PERCENTAGE:")
print("Median Red 3 Path: ", median_red_path_3_percentage, "%", sep="")

mean_red_path_4_percentage = calculate_mean_path_percentage(log, "RED PATH 4 PERCENTAGE:")
print("Mean Red 4 Path: ", mean_red_path_4_percentage, "%", sep="")

median_red_path_4_percentage = calculate_median_path_percentage(log, "RED PATH 4 PERCENTAGE:")
print("Median Red 4 Path: ", median_red_path_4_percentage, "%", sep="")

mean_sum_red_path_percentage = calculate_mean_path_percentage(log, "SUM RED PATH'S PERCENTAGE:")
print("-> Mean All Red Paths: ", mean_sum_red_path_percentage, "%", sep="")

median_sum_red_path_percentage = calculate_median_path_percentage(log, "SUM RED PATH'S PERCENTAGE:")
print("-> Median All Red Paths: ", median_sum_red_path_percentage, "%", sep="")

print("---")

mean_blue_path_percentage = calculate_mean_path_percentage(log, "BLUE PATH PERCENTAGE (Ammount count *2):")
print("Mean Blue Path: ", mean_blue_path_percentage, "%", sep="")

median_blue_path_percentage = calculate_median_path_percentage(log, "BLUE PATH PERCENTAGE (Ammount count *2):")
print("Median Blue Path: ", median_blue_path_percentage, "%", sep="")

mean_blue_path_3_percentage = calculate_mean_path_percentage(log, "BLUE PATH 3 PERCENTAGE (Ammount count *3):")
print("Mean Blue 3 Path: ", mean_blue_path_3_percentage, "%", sep="")

median_blue_path_3_percentage = calculate_median_path_percentage(log, "BLUE PATH 3 PERCENTAGE (Ammount count *3):")
print("Median Blue 3 Path: ", median_blue_path_3_percentage, "%", sep="")

mean_blue_path_4_percentage = calculate_mean_path_percentage(log, "BLUE PATH 4 PERCENTAGE (Ammount count *4):")
print("Mean Blue 4 Path: ", mean_blue_path_4_percentage, "%", sep="")

median_blue_path_4_percentage = calculate_median_path_percentage(log, "BLUE PATH 4 PERCENTAGE (Ammount count *4):")
print("Median Blue 4 Path: ", median_blue_path_4_percentage, "%", sep="")

mean_sum_blue_path_percentage = calculate_mean_path_percentage(log, "SUM BLUE PATH'S PERCENTAGE:")
print("-> Mean All Blue Paths: ", mean_sum_blue_path_percentage, "%", sep="")

median_sum_blue_path_percentage = calculate_median_path_percentage(log, "SUM BLUE PATH'S PERCENTAGE:")
print("-> Median All Blue Paths: ", median_sum_blue_path_percentage, "%", sep="")




