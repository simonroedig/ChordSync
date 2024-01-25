import re

# Log file path
log_file_path = "logs/easy_songs_to_learn_on_guitar.txt"

def count_sync_ratio_occurrences(log_content):
    sync_ratio_occurrences = log_content.count('SYNC RATIO:')
    return sync_ratio_occurrences

# Function to extract SYNC RATIO values
def extract_sync_ratios(log_content):
    sync_ratios = re.findall(r'SYNC RATIO: (\d+\.\d+)%', log_content)
    return sync_ratios

# Read log content from the file
with open(log_file_path, "r") as file:
    log_content = file.read()

# Extract SYNC RATIO values
sync_ratios = extract_sync_ratios(log_content)

# Remove percentage symbol and convert to float
sync_ratios = [float(ratio) for ratio in sync_ratios]

# Display the result
print("SYNC RATIO values:", sync_ratios)
print(len(sync_ratios), "values found")

# Get the count of SYNC RATIO occurrences
sync_ratio_count = count_sync_ratio_occurrences(log_content)

# Display the result
print("Number of SYNC RATIO occurrences:", sync_ratio_count)