import re

def replace_song_values(input_text):
    song_count = 0

    def replace_song(match):
        nonlocal song_count
        song_count += 1
        return f"SONG: {song_count}"

    # Use regular expression to find and replace SONG values
    result = re.sub(r"SONG: \d+", replace_song, input_text)

    return result

# Read input text file
input_file_path = 'logs/fix.txt'
with open(input_file_path, 'r') as file:
    input_text = file.read()

# Process the input text
output_text = replace_song_values(input_text)

# Write the processed text to a new file
output_file_path = 'output_file.txt'
with open(output_file_path, 'w') as file:
    file.write(output_text)

print("Replacement completed. Check output_file.txt.")